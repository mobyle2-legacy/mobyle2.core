########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################


import os , sys
import logging
from time import localtime, strftime , strptime

a_log = logging.getLogger( __name__ )

from Mobyle.MobyleError import MobyleError

class Admin:
    """
    manage the informations in the .admin file.
    be careful there is no management of concurrent access file
    thus if there is different instance of Admin with the same path
    it could be problem of data integrity
    """
    FIELDS = ( 'DATE'    ,
               'EMAIL'   ,
               'REMOTE'  ,
               'SESSION' ,
               'WORKFLOWID' ,
               'JOBNAME' ,
               'JOBID'   ,
               'MD5'     ,
               'EXECUTION_ALIAS' ,
               'NUMBER'  ,
               'QUEUE'
               )
    FILENAME = '.admin'

    def __init__( self, path ):
        self.me = {}
        path = os.path.abspath( path )

        if os.path.exists( path ):
            if os.path.isfile( path ):
                self.path = path
                self._parse()
            elif os.path.isdir( path ):
                self.path = os.path.join( path , Admin.FILENAME )
                if os.path.isfile( self.path ):
                    self._parse()
                else:
                    raise MobyleError , "invalid job path : " + self.path
        else:
            raise MobyleError , "invalid job path : " + path


    @staticmethod
    def create( path , remote , jobName , jobID , userEmail =None , sessionID = None , workflowID = None ):
        """create a minimal admin file"""
        adm_file = os.path.join( path , Admin.FILENAME )
        if os.path.exists( adm_file ):
            raise MobyleError , "an \"admin\" file already exist in %s. can't create a new one" % ( path )

        args = {'DATE' : strftime( "%x %X" , localtime() ) ,
                'REMOTE' : remote ,
                'JOBNAME' : jobName ,
                'JOBID' : jobID ,
                }
        if userEmail:
            args[ 'EMAIL'] = userEmail
        if sessionID:
            args[ 'SESSION' ] = sessionID
        if workflowID:
            args[ 'WORKFLOWID' ] = workflowID

        adminFile = open( adm_file , "w" )
        for key in Admin.FIELDS:
            try:
                value = args[ key ]
            except KeyError :
                continue
            adminFile.write( "%s : %s\n" %( key , value ) )
        adminFile.close()


    def __str__( self ):
        res = ''
        for key in self.__class__.FIELDS:
            try:
                if key == 'DATE':
                    value = strftime( "%x %X" , self.me['DATE'] )
                else:
                    value =  self.me[ key ]
            except KeyError :
                continue
            res = res + "%s : %s\n" % ( key , value )
        return res


    def _parse ( self ):
        """
        parse the file .admin
        """
        try:
            fh = open( self.path , 'r' )

            for line in fh:
                datas = line[:-1].split( ' : ' )
                key = datas[0]
                value = ' : '.join( datas[1:] )
                if key == 'DATE':
                    value = strptime( value , "%x %X" )
                self.me[ key ] = value
        except Exception , err :
            a_log.critical( "an error occured during %s/.admin parsing (call by: %s) : %s " %( self.path ,
                                                                                               os.path.basename( sys.argv[0] ) ,
                                                                                               err ) ,
                                                                                               exc_info = True  )
            raise MobyleError , err
        finally:
            try:
                fh.close()
            except:
                pass
            if not self.me:
                msg = "admin %s object cannot be instantiated: is empty ( call by %s ) " % ( self.path , os.path.basename( sys.argv[0] ) )
                a_log.critical( msg)


    def refresh( self ):
        self._parse()

    def commit( self ):
        """
        Write the string representation of this instance on the file .admin
        """
        if not self.me.values():
            msg = "cannot commit admin file %s admin instance have no values (call by %s) " % ( self.path ,  os.path.basename( sys.argv[0] ) )
            a_log.critical( msg )
        try:
            tmpFile = open( "%s.%d" %( self.path , os.getpid() ) , 'w' )
            tmpFile.write( self.__str__() )
            os.rename( tmpFile.name , self.path )
        except Exception , err :
            a_log.critical( "an error occured during %s/.admin commit (call by: %s) : %s " %( self.path ,
                                                                                               os.path.basename( sys.argv[0] ) ,
                                                                                               err ) ,
                                                                                               exc_info = True  )
            raise MobyleError , err
        finally:
            try:
                tmpFile.close()
            except:
                pass

    def getDate( self ):
        """
        @return: the date of the job submission
        @rtype: time.struct_time
        """
        try:
            return  self.me[ 'DATE' ]
        except KeyError :
            return None

    def getEmail( self ):
        """
        @return: the email of the user who run the job
        @rtype: string
        """
        try:
            return self.me[ 'EMAIL' ]
        except KeyError :
            return None

    def getRemote( self ):
        """
        @return: the remote of the job
        @rtype: string
        """
        try:
            return self.me[ 'REMOTE' ]
        except KeyError :
            return None

    def getSession( self ):
        """
        @return: the Session path of the job
        @rtype: string
        """
        try:
            return self.me[ 'SESSION' ]
        except KeyError :
            return None

    def getWorkflowID( self , default= None ):
        """
        @return: the Workflow owner the job
        @rtype: string
        """
        try:
            return self.me[ 'WORKFLOWID' ]
        except KeyError :
            return default


    def getJobName( self ):
        """
        @return: the name of the job ( blast2 , toppred )
        @rtype: string
        """
        try:
            return self.me[ 'JOBNAME' ]
        except KeyError :
            return None

    def getJobID( self ):
        """
        @return: the job identifier.
        @rtype: string
        """
        try:
            return self.me[ 'JOBID' ]
        except KeyError :
            return None

    def getMd5( self ):
        """
        @return: the md5 of the job
        @rtype: string
        """
        try:
            return self.me[ 'MD5' ]
        except KeyError :
            return None

    def setMd5( self , md5 ):
        """
        set the md5 of the job
        @param : the identifier of the job
        @type : string
        """
        self.me[ 'MD5' ] = md5

    def getExecutionAlias( self ):
        """
        @return: the ExecutionConfig alias corresponding to the Execution object used to run the job
        @rtype: string
        """
        try:
            return self.me[ 'EXECUTION_ALIAS' ]
        except KeyError :
            return None

    def setExecutionAlias( self , execution_alias ):
        """
        set the execution class name  used to run of the job
        @param :  alias of the ExecutionConfig its value must belong to
         ExecutionConfig in Config.EXECUTION_CONFIG_ALIAS keys.
        @type : string
        """
        self.me[ 'EXECUTION_ALIAS' ] = execution_alias

    def getNumber( self ):
        """
        @return: the number the job the meaning of this value depend of BATCH value.
         - BATCH = Sys number is the job pid
         - BATCH = SGE number is the result of qstat
        @rtype: string
        """
        try:
            return self.me[ 'NUMBER' ]
        except KeyError :
            return None


    def setNumber( self , number ):
        """
        set the number of the job this number depend of the batch value
        if BATCH = Sys number is the pid
        if BATCH = SGE number is the
        @param : the number of the job
        @type : string
        """
        self.me[ 'NUMBER' ] = number

    def getQueue( self ):
        """
        @return: return the queue name of the job
        @rtype: string
        """
        try:
            return self.me[ 'QUEUE' ]
        except KeyError :
            return None


    def setQueue( self, queue ):
        """
        set the queue name of the job
        @param : the queuename of the job
        @type : string
        """
        self.me[ 'QUEUE' ] = queue


