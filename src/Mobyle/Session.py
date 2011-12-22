########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

import sys
import os 
import types
import glob
from time import time , strptime 
import urlparse
from httplib import HTTPConnection
from logging  import getLogger
from lxml import etree

from Mobyle.Utils import safeFileName , sizeFormat
from Mobyle.JobState import JobState , path2url , url2path
from Mobyle.MobyleError import MobyleError , UserValueError , SessionError , NoSpaceLeftError 
from Mobyle.JobFacade import JobFacade
from Mobyle.Registry import registry

from Mobyle.Transaction import Transaction


class Session( object ):
    """
    This class defines a session, that stores all the information
    about a user that should be persistent on the server
    @author: Bertrand Neron
    @organization: Institut Pasteur
    @contact: mobyle@pasteur.fr
    """

    FILENAME = '.session.xml'

    def __init__( self , Dir , key , cfg ):
        
        self.log = getLogger( 'Mobyle.Session' )
        self.cfg = cfg
        """the maximum size of a session ( in bytes )"""
        self.sessionLimit = self.cfg.sessionlimit()
        self.key = str( key )
        """ the user/session  key"""
        self.Dir = Dir
        """ the absolute path to this session directory """


    def isLocal(self):
        """
        we cannot instanciate a distant session
        """
        return True
   
    def getDir( self ):
        """
        @return: the absolute path to this session
        @rtype: string
        """
        return self.Dir
    
    def getKey( self ):
        """
        @return: the session key
        @rtype: string
        """
        return  self.key

    def _getTransaction( self , Type ):
        """
        @return: the transaction of this session
        @rtype: a L{Transaction} object
        @raise SessionError: if can't access to the session
        """
        fileName = os.path.normpath( os.path.join( self.Dir , Session.FILENAME  ) )
        try:
            return Transaction( fileName , Type )
        except Exception , err:
            msg = "can't open transaction %s : %s" % ( self.getKey() , err )
            self.log.error( msg , exc_info= True )
            raise SessionError , "can't open user session. Please contact <%s> for help" % self.cfg.mailHelp()
      
       
    def getBaseInfo( self ):
        """
        @return: 3 basic informations about this session , the email , isAuthenticated , isActivated
        @rtype: ( string email , boolean isAuthenticated , boolean isActivated )
        """
        transaction = self._getTransaction( Transaction.READ  )
        response = ( transaction.getEmail() , transaction.isAuthenticated() , transaction.isActivated() )
        transaction.commit( )
        self.log.debug( "%f : %s : baseInfo return : %s" %( time() , self.getKey() , response ) )
        return response
   
    def isActivated( self ) :
        """
        @return: True if the session is activated, False otherwise
        @rtype: boolean
        """
        transaction = self._getTransaction( Transaction.READ  )
        activated = transaction.isActivated()
        transaction.commit()      
        return activated
    
    def  getEmail(self):
        """
        @return: the user email address
        @rtype: string
        """
        transaction = self._getTransaction( Transaction.READ )
        email = transaction.getEmail()
        transaction.commit()
        return email

    def setEmail( self, email ):
        """
        set the user email in the session
        @param email: the user email
        @type email: a Mobyle.Net.Email instance
        """
        if  isinstance( email , types.StringTypes ):
            from Mobyle.Net import EmailAddress
            email = EmailAddress( email )
        chk = email.check()
        if not chk:
            msg = email.getMessage()
            userMsg = "you are not allowed to run on this server for now "
            remoteLog = "UNKNOWN"
            try:
                remoteLog = os.environ[ 'REMOTE_ADDR' ]
            except KeyError:
                pass
            try:
                remoteLog = os.environ[ 'REMOTE_HOST' ]
            except KeyError:
                pass
                
            msg = "session/%s %s %s FORBIDDEN %s" % ( self.getKey() ,
                                                      unicode( str( email ).decode('ascii', 'replace')).encode( 'ascii', 'replace' ) ,
                                                      remoteLog ,
                                                      msg
                                                    )
    
            self.log.info( msg )
            raise UserValueError( msg = userMsg )
            
        transaction = self._getTransaction( Transaction.WRITE )
        transaction.setEmail( email )
        transaction.commit()

    ##############################
    #
    #   data methods
    #
    ###############################

    def _cleanData( self , content , dataType ):
        """
        clean the data send by the user, the cleaning depends of the parameter ( CRLF for Text etc...)
        and calculate it's md5. the md5 is based on the data content and the datatype
        @return: the data after cleaning , and the md5 
        @rtype: ( string md5 , string data content )
        """
        from hashlib import md5
        content = dataType.cleanData( content )
        newMd5 = md5()
        newMd5.update( content )
        #the md5 is made on the content + the name of the datatype
        #this permit us to have the same content wit 2 datatype.
        #eg a fasta alignment could be used as alignment or sequence        
        newMd5.update( dataType.getName() )
        dataID = newMd5.hexdigest()
        return dataID , content
    
    
    def addData( self , name  , mobyleType , content = None , producer = None , inputModes = [] , usedBy = [] , producedBy = []):
        """
        @param name: the data name
        @type name: string
        @param mobyleType: the type of the data
        @type mobyleType: a L{MobyleType} instance
        @param content: the content of the data
        @type content: string
        @param producer: where to find the data if content is None producer must be specify and vice & versa
        @type producer: a L{Job} , a L{MobyleJob} , or a L{Session} object
        @param inputModes: the source of data
        @type inputModes: a list of string among this values : 'db' , 'paste' , 'upload' , 'result'
        @param usedBy: jobID(s) which used this data as input
        @type usedBy: string or sequence of strings
        @param producedBy: jobID(s) which produced this data
        @type producedBy: string or sequence of strings   
        @return: the identifier of the data in this session
        @rtype: string
        """
        if not mobyleType.isFile():
            raise MobyleError , "session/%s : Session could add only MobyleType which are file : %s" % ( self.getKey() , mobyleType.getDataType().getName() )
        #transaction = self._getTransaction( Transaction.WRITE )

        if content and producer :
            raise MobyleError , "you must specify either a content or a producer not the both"
        elif not ( content or producer ) :
            raise MobyleError , "you must specify either a content or a producer "

        self.log.info( "%f : %s : addData name = %s, producer= %s, mobyleType=%s, usedBy=%s, producedBy=%s, inputModes=%s" %(time() ,
                                                                                                                             self.getKey(),
                                                                                                                            name,
                                                                                                                            producer,
                                                                                                                            mobyleType,
                                                                                                                            usedBy,
                                                                                                                            producedBy,
                                                                                                                            inputModes
                                                                                                                            ))
           

        safeUserName = safeFileName( name )
        acceptedInputMode = ( 'db' , 'paste' , 'upload' , 'result' )
        if safeUserName == Session.FILENAME :
            #logger l'erreur dans adm et logs?
            raise MobyleError , "permission denied"
        if inputModes :   
            inputModesType = type( inputModes ) 
            if inputModesType == types.StringType:
                inputModes = [ inputModes ]
            for inputMode in inputModes :
                if inputMode not in acceptedInputMode :
                    raise MobyleError , "unknown source of data : %s" % inputMode
        if usedBy:
            jobType = type( usedBy )
            if  jobType == types.StringType :
                usedBy = [ usedBy ]
            elif jobType ==  types.ListType or jobType == types.TupleType:
                pass
            else:
                raise MobyleError
        else:
            usedBy = []
            
        if producedBy:
            jobType = type( producedBy )
            if  jobType == types.StringType :
                producedBy = [ producedBy ]
            elif jobType ==  types.ListType or jobType == types.TupleType:
                pass
            else:
                raise MobyleError
        else:
            producedBy = []      
       
        # to avoid md5 differences depending on the web client or platform
        # I clean the content prior to perform the md5
        # be careful the cleaning must be adapted to the parameter
        # it's not the same between text and binary parameter
        dataType = mobyleType.getDataType()
        if producer and isinstance( producer , Session ):
            #producer is a Session
            #I copy the metadata about the data from the session source
            try:
                data = producer.getData( name )
            except ValueError:
                msg = "the data %s does not exist in the session %s" % ( name , self.getKey() )
                self.log.error( msg )
                raise SessionError , msg
                
            nameInProducer = data[ 'dataName' ]
            safeUserName   = data[ 'userName' ]
            mobyleType     = data[ 'Type' ]
            dataBegining   = data[ 'dataBegin' ]
            usedBy         = data[ 'usedBy' ]
            producedBy     = data[ 'producedBy' ]
            inputModes     = data[ 'inputModes' ]
            dataID  = str( nameInProducer )
         
            dataMask = os.path.join( self.Dir , dataID + "*" )
         
        else:
            if content :
                nameInProducer = None
                dataID , content = self._cleanData( content , dataType )
                dataBegining = dataType.head( content )
            else :
                #there is a producer and it's a jobState or MobyleJob ...
                #I must read the file to compute the md5

                #the name is Safe            
                fh = producer.open( name )
                content = fh.read()
                fh.close() 
                nameInProducer = name    
                dataID , content = self._cleanData( content , dataType )
                dataBegining = dataType.head( content )
                content = None 
                
            userExt = os.path.splitext( safeUserName )[1]
            dataMask = os.path.join( self.Dir , dataID + "*" )
            dataID = str( dataID + userExt )

        #for all 
        #absDataPath = os.path.join( self.Dir , dataID )
        files_exists = glob.glob(  dataMask  )
      
        if files_exists : 
            #it's important to recalculate the name in session 
            #because the ext must be different ( upload / copy&paste )
            #and the name return by file_exist is an absolute name and a local name in the data structure
            dataID = os.path.basename( files_exists[0] )
            transaction = self._getTransaction( Transaction.READ )
            try:
                data  = transaction.getData( dataID )
                transaction.commit()
            except ValueError : #the file exist but there is no entry in session
                transaction.rollback()
                msg = "inconsistency error between the session object and the directory"
                self.log.error("session/%s addDatas: %s" %( self.getKey() , msg ))
                try:
                    name2remove = os.path.join( self.Dir , dataID )
                    self.log.error("session/%s : remove the data %s before to add a new one " %( self.getKey() , name2remove ) )
                    os.unlink( name2remove )
                except IOError , err:
                    self.log.error("session/%s : can't remove it before to add a new one : %s" %( self.getKey() , err ) )
                #I add the data in transaction 
                self._createNewData( safeUserName , 
                                     content , 
                                     dataID , 
                                     producer , 
                                     nameInProducer , 
                                     mobyleType , 
                                     dataBegining , 
                                     producedBy = producedBy ,
                                     usedBy = usedBy ,
                                     inputModes = inputModes )
 
                return dataID 

            # the file exist and the data has already an entry in session.xml. thus I don't create a new data 
            # but this data is used/produced by a new job
            # furthermore, to ensure the coherence between data and jobs I check if the data is in job
            transaction = self._getTransaction( Transaction.WRITE )
            if usedBy:
                transaction.linkJobInput2Data( [ dataID ] , usedBy )
            if producedBy:
                transaction.linkJobOutput2Data( [ dataID ] , producedBy )
            transaction.commit()
            return dataID 
     
        else: #this data doesn't exist in Session
            # the disk writing operation or link is made by setValue.
            # more precisely by _toFile called by convert called by setValue of this parameter
            self._createNewData( safeUserName , 
                                 content , 
                                 dataID , 
                                 producer , 
                                 nameInProducer , 
                                 mobyleType , 
                                 dataBegining , 
                                 usedBy = usedBy , 
                                 producedBy = producedBy ,
                                 inputModes = inputModes )
            return dataID 
   
    def addWorkflow(self, workflow):
        """
        create a new workflow (or save a given Workflow object with a new ID)
        @param workflow: the workflow to be saved
        @type workflow: Workflow
        @return: the identifier of the workflow in this session
        @rtype: string
        """
        transaction = self._getTransaction( Transaction.WRITE )
        # set id
        ids = [value['id'] for value in transaction.getWorkflows()]
        if ids:
            ID = max(ids)+1
        else:
            ID = 1
        workflow.id = ID
        self.saveWorkflow(workflow)
        transaction.addWorkflowLink(workflow.id)
        transaction.commit()
        return workflow.id

    def getWorkflows(self):
        """
        get the list of workflow definitions in the session.
        @return: workflow definition identifiers list
        @rtype: [ {'id':string } , ... 
        """
        transaction = self._getTransaction( Transaction.READ )
        workflows = transaction.getWorkflows()
        transaction.commit()
        return workflows  

    def saveWorkflow(self, workflow):
        """
        save a new workflow version
        @param workflow: the workflow to be saved
        @type workflow: Workflow
        """
        # save workflow
        wffile = open( os.path.join(self.getDir(),'workflow%s.xml' % str(workflow.id)) , 'w' )
        wffile.write( etree.tostring(workflow, xml_declaration=True , encoding='UTF-8', pretty_print= True )) 
        wffile.close()

    def readWorkflow(self, ID):
        """
        read a workflow from the session
        @param ID: the id of the workflow to be read
        @type ID: string
        """
        # save workflow
        from Mobyle.Workflow import parser, MobyleLookup
        parser.set_element_class_lookup(MobyleLookup())
        return etree.parse(os.path.join(self.getDir(), 'workflow%s.xml' % str(id)), parser).getroot()

    def getWorkflowUrl(self, ID):
        """
        return the url of a workflow
        @param id: the id of the workflow to be read
        @type id: string
        """
        return self.url+'/workflow%s.xml' % ID

    def _createNewData(self , safeUserName , content , dataID , producer , nameInProducer , mobyleType , dataBegining , usedBy = None , producedBy = None ,  inputModes = None ):
        """
        @param safeUserName: the user name for this  data
        @type safeUserName: string
        @param content: the content of the data
        @type content: string
        @param dataID: the identifier of this data in the session
        @type dataID: string
        @param producer: where to find the data if content is None producer must be specify and vice & versa
        @type producer: a L{Job} , a L{MobyleJob} , or a L{Session} object
        @param nameInProducer: the name of this data in the producer
        @type nameInProducer: string
        @param mobyleType: the MobyleType corresponding to this data
        @type mobyleType: L{MobyleType} instance
        @param dataBegining: the beginning (50 first chars )of the data
        @type dataBegining: string
        @param usedBy: jobID(s) which used this data as input
        @type usedBy: string or sequence of strings
        @param producedBy: jobID(s) which produced this data
        @type producedBy: string or sequence of strings   
        @param inputModes: the source of data
        @type inputModes: a list of string among this values : 'db' , 'paste' , 'upload' , 'result'
        @return: the identifier of the data in this session
        @rtype: string
        """     
        self.log.info( "%f : %s : _createNewData safeUserName = %s, dataID= %s, producer= %s, nameInProducer= %s, mobyleType=%s, usedBy=%s, producedBy=%s, inputModes=%s" %(time() ,
                                                                                                                                                                            self.getKey(),
                                                                                                                                                                            safeUserName,
                                                                                                                                                                            dataID,
                                                                                                                                                                            producer,
                                                                                                                                                                            nameInProducer,
                                                                                                                                                                            mobyleType,
                                                                                                                                                                            usedBy,
                                                                                                                                                                            producedBy,
                                                                                                                                                                            inputModes
                                                                                                                                                                            ) )
        try:
            #                 mobyleType.toFile( data    , dest , destFileName , src      , srcFileName     )
            fileName , size = mobyleType.toFile( content , self , dataID       , producer , nameInProducer  )
            detectedMobyleType = mobyleType.detect( ( self, fileName ) )
        except MobyleError , err : 
            self.log.error("_createNewData dans MobyleError: " , exc_info = True  )
            try:
                os.unlink( os.path.join( self.Dir , dataID ) )
            except OSError :
                pass
            raise MobyleError , err
        except Exception , err:
            self.log.critical( "Exception in _createNewData: %s" % self.getKey(), exc_info = True )
            raise err
        dataID = fileName
          
        if not self._checkSpaceLeft():
            path = os.path.join( self.Dir , dataID )
            size = os.path.getsize( path )
            os.unlink( path )
            self.log.info( "%f : %s : _addData unlink %s ( %d ) because there is no space in session"%( time() ,
                                                                                                       self.getKey(),
                                                                                                       dataID ,
                                                                                                       size
                                                                                                       ))
            self.log.error( "session/%s : the data %s ( %d ) cannot be added because the session size exceed the session limit ( %d )" %(
                                                                                                                                      self.getKey() ,           
                                                                                                                                      dataID ,
                                                                                                                                      size ,
                                                                                                                                      self.sessionLimit
                                                                                                                                      ) )
         
            raise NoSpaceLeftError , "this data cannot be added to your bookmarks, because the resulting size exceed the limit ( %s )" % sizeFormat( self.sessionLimit )
        #dataID , userName , size , dataBegining , inputModes , format = None , producedBy = [] , usedBy = []    
        #must be clean only the format information must be uniq
        transaction = self._getTransaction( Transaction.WRITE )
        #self.log.error( "self.Dir ="+str( self.Dir )+", dataID  = "+str( dataID ) ) 
        try:
            transaction.createData( dataID , 
                                    safeUserName , 
                                    os.path.getsize( os.path.join( self.Dir , dataID ) ) ,
                                    detectedMobyleType , 
                                    dataBegining ,
                                    inputModes , 
                                    usedBy = usedBy  ,
                                    producedBy = producedBy ,
                                    )
        except Exception, err:
            path = os.path.join( self.Dir , dataID )
            os.unlink( path )
            msg = "cannot create metadata in .session.xml for data named: %s (dataID= %s): %s"%( safeUserName,
                                                                                                           dataID ,
                                                                                                           err)
            self.log.error( msg )
            raise SessionError( msg )
        
        if usedBy:
            transaction.linkJobInput2Data( [ dataID ] , usedBy )
        if producedBy:
            transaction.linkJobOutput2Data( [ dataID ] , producedBy )
        transaction.commit()
        return dataID        
       

    def _checkSpaceLeft( self ):
        """
        @return: True if there is space disk available for this session, False otherwise
        @rtype: boolean
        """
        sessionSize = 0
        for f in os.listdir( self.Dir ):
            sessionSize += os.path.getsize( os.path.join( self.Dir  , f ) )
            if sessionSize > self.sessionLimit:  
                self.log.debug( "%f : %s : _checkSpaceLeft call by= %s size found = %d" %( time() ,
                                                                                       self.getKey()  , 
                                                                                       os.path.basename( sys.argv[0] ) ,
                                                                                       sessionSize
                                                                                       )) 
                return False
        return True       
       

    def removeData( self , dataID ):
        """
        remove the data from this session ( from the xml and the directory )
        @param dataID: the data identifier in this session
        @type dataID:string
        @raise SessionError: if the dataID does not match any data in the session
        """
        self.log.info( "%f : %s : removeData dataID= %s" %(time() ,
                                                           self.getKey(),
                                                           dataID
                                                           ) )
        if dataID == Session.FILENAME :
            self.log.error( "session/%s : can't remove file %s" %( self.getKey(), Session.FILENAME ) )
            raise MobyleError, "permission denied"

        fileName = os.path.join( self.Dir , dataID  )

        if os.path.exists( fileName ):
            try:
                os.unlink( fileName )
            except OSError , err:
                msg = str( err )
                self.log.critical( "session/%s : can't remove data : %s" %( self.key , msg ) )
                raise MobyleError , msg
        transaction = self._getTransaction( Transaction.WRITE )
        try:
            transaction.removeData( dataID )
        except ValueError , err :
            transaction.rollback()
            self.log.error( "session/%s : can't remove data in %s : %s" %( self.getKey() ,
                                                                      self.FILENAME ,
                                                                      err 
                                                                    ) 
                          )
            raise SessionError, err
        else:
            transaction.commit()
       
       
    def renameData( self , dataID  , newUserName ):
        """
          @param dataID: the identifier of the data in the session ( md5 )
          @type dataID: string
          @param newUserNAme: the new user name of this data
          @type newUserName: string
          @raise SessionError: if the dataID does not match any data in this session
        """
        self.log.info( "%f : %s : renameData dataID= %s, newUserName= %s" %(time() ,
                                                                            self.getKey(),
                                                                            dataID,
                                                                            newUserName
                                                                            ) )
        transaction = self._getTransaction( Transaction.WRITE )
        try:
            data = transaction.renameData( dataID , newUserName )
        except ValueError , err :
            transaction.rollback()
            raise SessionError , err
        else:
            transaction.commit()       
       
       
    def getContentData( self , dataID , forceFull = False ):
        """
        @param dataID: the identifier of the data in the session.
        @type dataID: string
        @return: the head or full content of the data
        @rtype: tuple ( string 'HEAD'/'FULL' , string content )
        @raise SessionError: if dataID doesn't match any data in session
        """
        maxSize = self.cfg.previewDataLimit()
        filename = os.path.join( self.Dir , dataID  )
      
        if not os.path.exists( filename ):
            transaction = self._getTransaction( Transaction.READ )
            hasData = transaction.hasData( dataID )
            transaction.commit()
            if hasData: #the data is not in the session directory But in the session data structure
                self.log.error( "session/%s is corrupted. The data %s is not in directory But in data structure" % ( self.getKey(),
                                                                                                                    dataID
                                                                                                                    )
                                                                                                                    )
                transaction = self._getTransaction( Transaction.WRITE )
                transaction.removeData( dataID )
                transaction.commit()
                self.log.error( "session/%s remove data %s" % ( self.getKey() , dataID ))
            else: #the data is neither in the session directory nor the session data structure 
                raise SessionError, "%s  No such data in session: %s" % ( self.getKey() , dataID )
      
        fh = self.open( dataID )
        if forceFull:
            content = fh.read()
            flag = 'FULL'
        else:
            dataSize = os.path.getsize( filename )
            if dataSize > maxSize :
                content = fh.read( maxSize )
                flag = 'HEAD'
            else:
                content = fh.read()
                flag = 'FULL'            
      
        fh.close()
        return ( flag , content )
  
  
  
    def open( self , dataID ):
        """
        @param dataID: the identifier of the data in the session.
        @type dataID: string
        @return: a file object
        @retype: 
        @raise SessionError: if dataID does not match any data in session
        """
        self.log.debug( "%f : %s  open dataName = %s" %( time(),
                                                      self.getKey() ,
                                                      dataID 
                                                      ))
        if dataID == Session.FILENAME:
            raise MobyleError , "permission denied"
        try:
            fh = open( os.path.join( self.Dir , dataID ), 'r' )
            return fh
        except IOError, err:
            #verifier si la donnee est toujours dans la session
            self.log.error( "session/%s : open : %s" %( self.getKey() , err ) )
            raise SessionError , err  
  
  
  
    def getDataSize(self , dataID ):
        """
        @param dataID: the identifier of the data in the session.
        @type dataID: string
        @return: the size of the data in byte
        @rtype: int
        """
        #I don't use the size stored in transaction.datas[ 'size' ] 
        #to avoid to put a lock on the .session file
        dataPath =  os.path.join( self.Dir , dataID )
        if os.path.exists(  dataPath ):
            return os.path.getsize( dataPath )
        else:
            msg = "getDataSize dataID %s does not match any data in the session %s" % (dataID , self.getKey() ) 
            self.log.error( msg )
            raise SessionError , msg 


    def hasData( self , dataID ):
        """
        @param dataID: the identifier of this data in the session 
        @type dataID: string
        @return: True if this session has an entry for this data, False otherwise.
        this method does not test the existence of the data as file in session.
        @rtype: boolean        
        """
        transaction = self._getTransaction( Transaction.READ )
        hasData = transaction.hasData( dataID )
        transaction.commit()
        return hasData
    
    def getAllData( self ):
        """
        @return: the all data in the session. 
        @rtype: list of dict
                 [   {  'dataName'  : string ,
                        'userName'  : string ,                
                        'Type'      : ( string  , string )
                        'dataBegin' : string , 
                        'inputModes': list of strings ,
                        'producedBy': list of strings ,
                         'usedBy'   : list of strings 
                    } , ... 
                 ]   
        @raise SessionError: 
        """

        transaction = self._getTransaction( Transaction.READ )
        datas = transaction.getAllData()
        transaction.commit()
        return datas  

    
    def getData(self , dataID ):
        """
        @param dataID: the ID of the data in the session
        @type dataID: string or sequence of string
        @return: the data in the session corresponding to dataID 
        @rtype: dict
                  { 'dataName'  : string ,
                    'userName'  : string ,                
                    'type'      : MobyleType
                    'dataBegin' : string , 
                    'inputModes': list of strings ,
                    'producedBy': list of strings ,
                    'usedBy'   : list of strings 
                } 
        @raise SessionError: if dataID does not match any data in session     
        """
        transaction = self._getTransaction( Transaction.READ )
        try:
            data = transaction.getData( dataID )
            transaction.commit()
        except ValueError:
            transaction.rollback()
            msg = "getData dataID %s does not match any data in the session %s" % (dataID , self.getKey() ) 
            self.log.error(msg)
            raise SessionError , msg
        return data
  

    def __extractServiceName( self , jobID ):
        """
        @param jobID: the url of a job 
        @type job: string
        @return: the program name for a job
        @rtype string
        """
        s = jobID.split('/')
        if s[-1] == '' or s[-1] == 'index.xml':
            return s[ -3  ]
        else:
            return s[ -2 ]


    def getAllUniqueLabels( self):
        """
        set description for the jobId
        """
        transaction= self._getTransaction(Transaction.READ)
        
        labelsList = transaction.getAllUniqueLabels()
        transaction.commit()
        return labelsList

    def getJobLabels( self, jobID ):
        """
        @return: the labels for job with identifier jobID
        @rtype: list of strings , [ string label1 ,string label2 ,...] or None if this jobs has no labels. 
        @param jobID: the job identifier (it's url) of a job
        @type jobID: string
        @raise ValueError: if there is no job with jobID in the session
        """
        transaction= self._getTransaction(Transaction.READ)
        labels = transaction.getJobLabels( jobID )
        transaction.commit()
        return labels
    
    def setJobLabels( self, jobID, inputLabels):
        """
        set labels for job with  jobId
        @param jobID: the job identifier (it's url) of a job
        @type jobID: string
        @param description: the description of this job
        @type description: string
        @raise ValueError: if there is no job with jobID in the session
        """
        transaction= self._getTransaction(Transaction.WRITE)
        transaction.setJobLabels( jobID, inputLabels)
        transaction.commit()


    def setJobDescription( self, jobID, description):
        """
        set description for the job with jobId
        @param jobID: the job identifier (it's url) of a job
        @type jobID: string
        @param description: the description of this job
        @type description: string
        @raise ValueError: if there is no job with jobID in the session
        """
        transaction= self._getTransaction(Transaction.WRITE)
        transaction.setJobDescription( jobID, description )
        transaction.commit()

    def getJobDescription( self, jobID):
        """
        @return: the description for job with identifier jobID
        @rtype: string or None if there is no description for this job 
        @param jobID: the job identifier (it's url) of a job
        @type jobID: string
        @raise ValueError: if there is no job with jobID in the session
        """
        transaction= self._getTransaction(Transaction.READ)
        desc = transaction.getJobDescription( jobID )
        transaction.commit()
        return desc
      

    def hasJob(self , jobID ):
        """
        @param jobID: the url of a job 
        @type job: string
        @return: True if this session has an entry for this job, False otherwise.
        this method does not test the existence of the job as directory.
        @rtype: boolean        
        """
        transaction = self._getTransaction( Transaction.READ )
        hasJob = transaction.hasJob( jobID )
        transaction.commit()
        return hasJob
    

    def getAllJobs( self ):
        """
        @return: the list of jobs (and update their status) 
        @rtype: list of dictionary = [  { 'jobID'       : string ,
                                          'userName'    : string , 
                                          'programName' : string ,
                                          'date'        : time.time_struct ,
                                          'status'      : Status.Status ,
                                          'dataUsed'    : [ md5name ] ,
                                          'dataProduced : [ md5name ] ,
                                        } , ...
                                    ]
        """
        results = []
        job2remove = []
        job2updateStatus = []
        
        transaction = self._getTransaction( Transaction.READ )
        jobs = transaction.getAllJobs()
        transaction.commit()
        for job in jobs:
            jobExist = self.jobExists(job[ 'jobID' ])
            if jobExist == 1: #yes
                job[ 'jobPID' ] = registry.getJobPID(job['jobID'])
                results.append( job )
                jf = JobFacade.getFromJobId( job[ 'jobID' ] )
                job['subjobs']  = jf.getSubJobs() 
                if job[ 'status' ].isQueryable():
                    newStatus = jf.getStatus()
                    if newStatus != job[ 'status' ]:
                        job[ 'status' ] = newStatus
                        job2updateStatus.append( ( job[ 'jobID' ] , newStatus ) )
            elif jobExist == 2 :# maybe
                results.append(job)
            else: #the job does not exists anymore
                job2remove.append(job[ 'jobID' ])
        
        if job2remove or job2updateStatus :
            transaction = self._getTransaction(Transaction.WRITE)
            for jobID in job2remove:
                try:
                    transaction.removeJob( jobID )
                except ValueError:
                    continue
            for jobID , newStatus in job2updateStatus:
                try:
                    transaction.updateJobStatus( jobID , newStatus )
                except ValueError:
                    self.log.error( "can't update status. the job %s does not exist in session %s" %( jobID , self.getKey() ) )
                    continue
            transaction.commit()
        return results
    
    
    def getJob(self , jobID ):
        """
        @param jobID: the url of a job 
        @type job: string
        @return: the job corresponding to the jobID
        @rtype: dict { 'jobID'       : string ,
                       'userName'    : string , 
                       'programName' : string ,
                       'date'        : time.time_struct ,
                       'status'      : Mobyle.Status.Status instance,
                       'dataUsed'    : [ string md5name ] ,
                       'dataProduced : [ string md5name ] ,
                     }
        @raise SessionError: if the jobID does not match any job in this session
        """
        transaction = self._getTransaction( Transaction.READ )
        try:
            job = transaction.getJob( jobID )
        except ValueError:
            transaction.rollback()
            msg = "getJob jobID %s does not match any job in the session %s" %(jobID , self.getKey() ) 
            self.log.error(msg )
            raise SessionError , msg
        
        transaction.commit()
        jobExist = self.jobExists( jobID ) 
        if jobExist == 1: #yes 
            if job[ 'status' ].isQueryable():
                #cannot be replaced by call to StatusManager.getStatus
                #because the job may be remote
                jf = JobFacade.getFromJobId( jobID )
                newStatus = jf.getStatus() 
                if newStatus != job[ 'status' ]:
                    job[ 'status' ] = newStatus
                    try:
                        transaction = self._getTransaction( Transaction.WRITE )
                        transaction.updateJobStatus(  jobID , newStatus  )
                        transaction.commit()
                    except ValueError:
                        transaction.rollback()
                        self.log.error( "can't update status. the job %s does not exist in session %s" % (jobID, self.key ))                    
                        #inconsistance entre la transaction et mon resultat
                        #la transaction a evolue de puis le getJob, via un acces concurrent ??
                        return None
            return job
        elif jobExist == 2 :# maybe
            return job
        else: #the job does not exists anymore
            try:
                transaction = self._getTransaction( Transaction.WRITE )
                transaction.removeJob( jobID )
                transaction.commit()
            except ValueError:
                transaction.rollback()
                msg = "getJob jobID %s does not match any job any more in the session %s" % (jobID , self.getKey() ) 
                self.log.error(msg )
            return None
    
    #OPENID 
    def addOpenIdAuthData(self, authsession):
        """
        @param authsession: the session used by OpenId library
        @type authsession: Session
        @raise SessionError : if data cannot be saved
        """
        transaction = self._getTransaction( Transaction.WRITE )
        try:
            transaction.addOpenIdAuthData( authsession )
            transaction.commit()
        except ValueError:
            transaction.rollback()
            msg = "Error setting auth data"
            self.log.error( msg )
            raise SessionError , msg
    #OPENID
    def getOpenIdAuthData(self):
        """
        @return : Session with openid data
        @raise SessionError : if data cannot be read
        """
        transaction = self._getTransaction( Transaction.READ )
        try:
            authsession = transaction.getOpenIdAuthData()
        except ValueError :
            transaction.rollback()
            msg = "Could not get auth data"
            self.log.error(msg )
            raise SessionError , msg
        transaction.commit()
        return authsession
        
    
    def renameJob( self , jobID  , newUserName ):
        """
        @param jobID: the name of the job in the session (url)
        @type jobID: string
        @param newUserNAme: the new user name of this job
        @type newUserName: string
        @raise SessionError: if the jobID does not match any job in this session
        """
        transaction = self._getTransaction( Transaction.WRITE )
        try:
            transaction.renameJob( jobID , newUserName )
            transaction.commit()
        except ValueError:
            transaction.rollback()
            msg = "There is no job with ID %s in session %s" % ( jobID , self.getKey() )
            self.log.error( msg )
            raise SessionError , msg

   
    
    def addJob( self, jobID  , userName = None , dataUsed = [] , dataProduced = [] ):
        """
        add a job in session 
        @param jobID: the ID (url) of a job 
        @type jobID: string
        @param dataUsed: the name of data used by this job ( md5Name )
        @type dataUsed: string or sequence of strings
        @param dataProduced: the name of data produced by this job ( md5Name )
        @param dataProduced: string or sequence of strings
        """
        if isinstance( dataUsed , types.StringType ) :
            dataUsed = [ dataUsed ]
    
        if isinstance( dataProduced , types.StringType ):
            dataProduced = [ dataProduced ]
        jf = JobFacade.getFromJobId( jobID )
        jobState = JobState( jobID )
        if not userName:
            userName = jobID
        programName = self.__extractServiceName( jobID )   
        status = jf.getStatus()
        date = strptime( jobState.getDate() , "%x  %X" )
            
        transaction = self._getTransaction( Transaction.WRITE )
        try:
            transaction.createJob( jobID , userName , programName , status , date , dataUsed ,  dataProduced )
            if dataUsed:
                transaction.linkJobInput2Data( dataUsed , [ jobID ])
            if dataProduced:
                transaction.linkJobOutput2Data( dataProduced , [ jobID ] )
            transaction.commit()
        except ValueError , err:
            transaction.rollback()
            self.log.error( str( err) )
            raise SessionError , err
        
    def removeJob(self , jobID ):
        """
        remove job from Session (in jobs and datas ) and ONLY in session. if the job is local and running kill the job.
        @param jobID: the url of a job
        @type job: string
        @raise SessionError: if the jobID does not match any job in this session
        """
        protocol , host , path , a, b, c = urlparse.urlparse( jobID  )
        if protocol != "http" :
            jobID = path2url( jobID )
        
        transaction = self._getTransaction( Transaction.WRITE )
        try:
            jobDict = transaction.removeJob( jobID )
        except ValueError:
            transaction.rollback()
            msg = "removeJob jobID %s does not match any job in the session %s" % (jobID , self.getKey() ) 
            self.log.error( msg )
            raise SessionError , msg
        else:
            transaction.commit()
            if jobDict[ 'status' ].isEnded():#'finished' , 'error' , 'killed' 
                return None #it doesn't usefull to kill it 
            
            if self.jobExists( jobID ) == True :
                jf = JobFacade.getFromJobId( jobID )
                status = jf.getStatus()
                if status.isQueryable():
                    try:
                        jf.killJob()
                    except MobyleError , err:
                        self.log.error( "session/%s removeJob can't kill job = %s : %s" % ( self.getKey() , jobID , err ) )
     
    def jobExists( self , jobID ): 
        """
        @return: return 1 if the job directory exists, 0 otherwise ( it does not check if the entry exists in session.xml ).
        for remote job, the existence of a job could not be decided ( remote server problem , timeout ...) in this case 
        return  2 
        @rtype: int
        """
        if jobID[-10:] == '/index.xml':
            jobID = jobID[:-10]
            
        server = registry.getServerByJobId(jobID)
        
        if server is None :
            self.log.warning('registry does not known this server: %s' % jobID )
            return 0
        if server.name == 'local':
            try:
                jobPath = url2path( jobID )
            except MobyleError:
                return 0
            return os.path.exists( jobPath )
        else: #this jobID correspond to a remote job
            try:
                status , newUri = self._connect( jobID + '/index.xml' ) 
                if status == 3:
                    for attempt in range(10):
                        status , newUri = self._connect( newUri )
                        if status != 3:
                            break
                    if status == 3:
                        self.log.error("we attempt 10 redirections whithout reaching the target url: %s" % jobID )
                        return 2
                if status == 2:
                    return 1
                if status == 4:
                    return 0
                else:
                    self.log.error( "%s : %s" %( jobID , status ) )                    
                    return 2      
            except Exception, e:
                self.log.error(e, exc_info=True)
                return 2   
   
    def _connect(self , url ):
        """
        
        """
        protocol , host , path , a, b, c = urlparse.urlparse( url )
        try:
            cn = HTTPConnection(host)
            cn.connect()
            cn.sock.settimeout( 10 ) #set the timeout to 10 sec
            cn.request( "HEAD" , url )
            resp = cn.getresponse()
            status = resp.status / 100
            newUri = resp.getheader('Location')
        except Exception , e:
            self.log.error( "job %s is unreachable : %s " %( url  , e )  )
            status = 5 #in http code 500 are for errors 
            newUri = url
        return status , newUri


    
