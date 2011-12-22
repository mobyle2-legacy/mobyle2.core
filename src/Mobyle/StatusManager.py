########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

import errno
from lxml import etree
import fcntl

from time import sleep , time

from Mobyle.Status import Status
from Mobyle.MobyleError import MobyleError
from Mobyle.Utils import parse_xml_file

import logging
_log = logging.getLogger( __name__ )

import sys
import os.path


class StatusManager(object):
    """
    This class is the main access to the job status
    """

    WRITE  = fcntl.LOCK_EX
    READ   = fcntl.LOCK_SH
    file_name = 'mobyle_status.xml'

    @classmethod
    def create( cls , job_path  , status ):
        fileName = os.path.join( job_path , cls.file_name )
        root = etree.Element( "status" )
        value_node  = etree.Element( "value" )
        root.append( value_node )
        message_node = etree.Element( "message" )
        root.append( message_node )
        value_node.text = str( status )
        message_node.text = status.message
        try:
            File = open(  fileName  , 'w' )
            File.write( etree.tostring( root , encoding='UTF-8' , pretty_print = True))
        except IOError , err:
            msg = "cannot create status %s : %s" % ( fileName , err )
            _log.error( msg )
            raise MobyleError( msg )
        finally:
            File.close()



    def _lock( self , File , lockType ):
        """
        try to acquire a lock of lockType on self.__File
        @raise IOError: when it could not acquire a lock
        """
        IGotALock = False
        _log.debug( "%f : %s : _lock Type= %s ( call by= %s )"  %( time() ,
                                                                        File.name,
                                                                        ( 'UNKNOWN LOCK', 'READ' , 'WRITE' )[ lockType ] ,
                                                                        os.path.basename( sys.argv[0] ) ,
                                                                        ))
        for attempt in range( 5 ):
            try:
                fcntl.lockf( File , lockType | fcntl.LOCK_NB )
                IGotALock  = True
                _log.debug( "%f : %s : _lock IGotALock = True" %(time() , File.name ))
                break
            except IOError , err:
                _log.debug( "%f : %s : _lock IGotALock = False" %(time() , File.name))
                sleep( 0.2 )

        if not IGotALock :
            _log.error( "%s : %s" %( File.name , err ) )
            _log.debug( "%f : %s : _lock Type= %s ( call by= %s )"  %( time() ,
                                                                            File.name ,
                                                                            ( 'UNKNOWN LOCK', 'READ' , 'WRITE' )[ lockType ] ,
                                                                            os.path.basename( sys.argv[0] )
                                                                            ))

            raise IOError , err


    def setStatus(self, job_path , status ):
        fileName = os.path.normpath( os.path.join( job_path , self.file_name ) )
        try:
            File = open( fileName , 'r+' )
        except IOError , err:
            if err.errno == errno.ENOENT :
                try:
                    return self._fall_back_setStatus( job_path , status )
                except Exception , err:
                    _log.error( "%s : cannot open either index.xml nor mobyle_status.xml: %s" % ( job_path , err ))
                    return Status( code= -1 )
            else:
                _log.error( "cannot open %s : %s" % ( fileName , err ))
                return Status( code= -1 )
        self._lock( File , self.WRITE ) #try to acquire a lock
        #If I do not got a lock a IOError is raised
        try:
            parser = etree.XMLParser( no_network = False )
            doc = parse_xml_file(File , parser)
            root = doc.getroot()
        except Exception , err:
            msg = "error in parsing status %s : %s" % ( File.name , err )
            _log.error( msg )
            _log.debug("%f : %s : setStatus UNLOCK " %( time() , fileName ) )
            fcntl.lockf( File , fcntl.LOCK_UN  )
            File.close()
            raise MobyleError( msg )
        #################
        old_status = self.getStatus( job_path )
        _log.debug( "old_status= %s" %old_status )
        if old_status.isEnded():
            _log.warning( "%f : %s : try to update job status from %s to %s ( call by %s )"%( time() ,
                                                                                              fileName ,
                                                                                              old_status ,
                                                                                              status ,
                                                                                              os.path.basename( sys.argv[0] )
                                                                                              ) )
            try:
                _log.debug("%f : %s : setStatus UNLOCK " %( time() , fileName ) )
                fcntl.lockf( File , fcntl.LOCK_UN  )
            except Exception , err :
                _log.error( "%f : %s : setStatus cannot UNLOCK : %s" %( time() , fileName , err ) )
            finally:
                File.close()
            return None
        try:
            value_node = root.find( "value" )
            value_node.text = str( status )
            message_node = root.find( "message" )
            message_node.text = status.message
        except Exception, err:
            msg = "error in parsing status %s : %s" % ( File.name , err )
            _log.error( msg )
            _log.debug("%f : %s : setStatus UNLOCK " %( time() , fileName ) )
            fcntl.lockf( File , fcntl.LOCK_UN  )
            File.close()
            raise MobyleError( msg )
        ##################
        try:
            tmpFile = open( "%s.%d" %( File.name , os.getpid() )  , 'w' )
            tmpFile.write( etree.tostring( root , xml_declaration=True , encoding='UTF-8' , pretty_print = True))
            os.rename( tmpFile.name , File.name )
        except IOError , err:
            msg = "cannot write status : " + str( err )
            _log.error( msg )
            raise MobyleError( msg )
        except Exception , err:
            _log.error( "cannot write status %s " % File.name , exc_info = True )
            raise err
        finally:
            try:
                _log.debug("%f : %s : setStatus UNLOCK " %( time() , fileName ) )
                fcntl.lockf( File , fcntl.LOCK_UN  )
                File.close()
                tmpFile.close()
            except Exception , err :
                _log.error( "%f : %s : setStatus cannot UNLOCK : %s" %( time() , fileName , err ) )



    def getStatus(self , job_path ):
        fileName = os.path.normpath( os.path.join( job_path , self.file_name ) )
        try:
            File = open( fileName , 'r' )
        except IOError , err:
            if err.errno == errno.ENOENT :
                try:
                    return self._fall_back_getStatus( job_path )
                except Exception , err:
                    _log.error( "%s : cannot open either index.xml nor mobyle_status.xml: %s" % ( job_path , err ))
                    return Status( code= -1 )
            else:
                _log.error( "cannot open %s : %s" % ( fileName , err ))
                return Status( code= -1 )
        try:
            self._lock( File, self.READ  ) #try to acquire a lock
            #If I do not got a lock a IOError is raised
        except IOError , err:
            _log.error( "%f : %s : cannot read status : %s" %( time() , fileName , err ) )
            return Status( code= -1 )
        try:
            parser = etree.XMLParser( no_network = False )
            doc = parse_xml_file( File , parser )
            root = doc.getroot()
        except Exception , err:
            pass
        finally:
            _log.debug("%f : %s : getStatus UNLOCK " %( time() , fileName ) )
            fcntl.lockf( File , fcntl.LOCK_UN  )
            File.close()
        try:
            value_node = root.find( "value" )
            message_node = root.find( "message" )
        except Exception , err:
            _log.error( "%f : %s : cannot parse status" %( time() , fileName ) , exc_info = True )
            return Status(code = -1)
        if message_node is None :
            return Status( string = value_node.text )
        else:
            return Status( string = value_node.text , message = message_node.text )



    def _fall_back_setStatus(self , job_path  , status ):
        parser = etree.XMLParser( no_network = False )
        index_path = os.path.join( job_path ,'index.xml')
        doc = parse_xml_file( index_path , parser)
        root = doc.getroot()
        status_node = root.find( "./status" )
        try:
            old_message = status_node.find( "value" )
            if old_message is None:
                oldStatus = Status( string = str( status_node.find( "value").text ) )
            else:
                oldStatus = Status( string = str( status_node.find( "value").text ) ,
                                    message = str( old_message.text )
                                    )
        except AttributeError:
            oldStatus = Status( code = -1 ) #unknown

        if oldStatus.isKnown() and oldStatus.isEnded():
            #the job is ended we can refactor status in a separate file
            root.remove( status_node )
            try:
                tmp_file = open( os.path.join( job_path ,'tmp_index.xml' ) , 'w' )
                tmp_file.write( etree.tostring( doc , pretty_print = True , encoding='UTF-8' ))
                tmp_file.close()
                os.rename( tmp_file.name , index_path )
            except Exception , err :
                _log.error( 'cannot make index.xml : %s' % err )

            self.create( job_path  , oldStatus )
            return None

        if status == oldStatus:
            #this is an old job with status managed by JobState
            #new status and old status will evolved
            #do nothing until job finish
            return None
        else:
            if status.isEnded():
                #the job is ended we can refactor status in a separate file
                root.remove( status_node )
                try:
                    tmp_file = open( os.path.join( job_path ,'tmp_index.xml' ) , 'w' )
                    tmp_file.write( etree.tostring( doc , pretty_print = True , encoding='UTF-8' ))
                    tmp_file.close()
                    os.rename( tmp_file.name , index_path )
                except Exception , err :
                    _log.error( 'cannot make index.xml : %s' % err )
                self.create( job_path  , status)
            else:
                #the job is not ended we update the index.xml
                value_node = status_node.find( 'value' )
                value_node.text = str( status )
                message_node = status_node.find( 'message' )
                if message_node is not None:
                    message_node.text = str( status.message )

                try:
                    tmpFile = open( "%s.%d" %( index_path , os.getpid() )  , 'w' )
                    tmpFile.write( etree.tostring( doc , xml_declaration=True , encoding='UTF-8' ))
                    tmpFile.close()
                    os.rename( tmpFile.name , index_path )
                except IOError, err:
                    _log.error( "IOError during write index.xml on disk")
                    raise MobyleError , err



    def _fall_back_getStatus(self , job_path ):
        parser = etree.XMLParser( no_network = False )
        doc = parse_xml_file( os.path.join( job_path ,'index.xml') , parser)
        root = doc.getroot()
        try:
            status = root.find( "./status/value" ).text
        except AttributeError:
            return Status( code = -1 ) #unknown
        try:
            message = root.find( "./status/message" ).text
        except AttributeError:
            message =  None
        if message:
            return Status( string = str( status ) , message = str( message ))
        else:
            return Status( string = str( status )  )
