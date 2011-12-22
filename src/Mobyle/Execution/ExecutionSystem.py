########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################


"""
Classes executing the command and managing the results  
"""
import os
import time

from logging import getLogger
_log = getLogger(__name__)

from Mobyle.ConfigManager import Config
from Mobyle.MobyleError import MobyleError
from Mobyle.Admin import Admin
from Mobyle.Status import Status
from Mobyle.StatusManager import StatusManager

__extra_epydoc_fields__ = [('call', 'Called by','Called by')]


class ExecutionSystem(object):
    """
    abstract class
    manage the status by updating the file index.xml
    """

    def __init__( self , execution_config  ):
        """
        @param execution_config: the configuration of the Execution 
        @type execution_config: ExecutionConfig instance
        """
        self._cfg = Config()
        self.execution_config = execution_config
        self.execution_config_alias = self._cfg.getAliasFromConfig( self.execution_config )
        self.status_manager = StatusManager()
    
    def run( self , commandLine , dirPath , serviceName , jobState , xmlEnv = None):
        """
        @param execution_config: the configuration of the Execution 
        @type execution_config: ExecutionConfig instance
        @param commandLine: the command to be executed
        @type commandLine: String
        @param dirPath: the absolute path to directory where the job will be executed (normaly we are already in)
        @type dirPath: String
        @param serviceName: the name of the service
        @type serviceName: string
        @param jobState:
        @type jobState: a L{JobState} instance
        """
        self.jobState = jobState
        if dirPath[-1] == '/':
            dirPath = dirPath[:-1]
        jobKey = os.path.split( dirPath )[1]
        if os.getcwd() != os.path.abspath( dirPath ):
            msg = "the child process execute itself in a wrong directory"
            self._logError( dirPath , serviceName ,jobKey,
                            userMsg = "Mobyle internal server error" ,
                            logMsg = msg  )
            raise MobyleError , msg 
        
        protectedCommandLine = ''
        for c in commandLine:
            protectedCommandLine += '\\'+ c
            
        if xmlEnv is None:
            xmlEnv = {}
            
        dispatcher = self._cfg.getDispatcher()
        queue = dispatcher.getQueue( jobState )
        adm = Admin( dirPath )
        adm.setQueue( queue )
        adm.commit()
        
        new_path = ''
        binary_path = self._cfg.binary_path()
        if binary_path :
                new_path = ":".join( binary_path )        

        if xmlEnv.has_key( 'PATH' ) :      
                new_path = "%s:%s" %( xmlEnv[ 'PATH' ] , new_path )
        if new_path :
            xmlEnv[ 'PATH' ] = "%s:%s" %( new_path , os.environ[ 'PATH' ] ) 
        else:
            xmlEnv[ 'PATH' ] = os.environ[ 'PATH' ] 
        for var in os.environ.keys():
            if var != 'PATH':
                xmlEnv[ var ] = os.environ[ var ]
        self._returncode = None
        accounting = self._cfg.accounting()
        if accounting:
            beg_time = time.time()

        ###################################
        mobyleStatus = self._run( commandLine , dirPath , serviceName , jobKey , jobState , queue , xmlEnv )
        ###################################
        
        if accounting:
            end_time = time.time()
            elapsed_time = end_time - beg_time
            a_log = getLogger( 'Mobyle.account' )
            #%d trunc time to second
            #%f for millisecond
            a_log.info("%(serviceName)s/%(jobkey)s : %(exec_class)s/%(queue)s : %(beg_time)d-%(end_time)d %(ela_time)d : %(status)s" %{ 'serviceName':serviceName ,
                                                                                                                          'jobkey':jobKey,
                                                                                                                          'exec_class':self.execution_config.execution_class_name ,
                                                                                                                          'queue': queue,
                                                                                                                          'beg_time':beg_time ,
                                                                                                                          'end_time':end_time ,
                                                                                                                          'ela_time':elapsed_time ,
                                                                                                                          'status': mobyleStatus ,
                                                                                                                          }
                                                                                                              )
        self.status_manager.setStatus( dirPath , mobyleStatus )


    def getStatus( self ,  number ):
        """
        @param execution_config: a configuration object for this execution system
        @type execution_config: an ExecutionConfig subclass instance
        @param number:
        @type number:
        @return the status of the job
        @rtype:
        abstract method. this method must be implemented in child classes
        """
        raise NotImplementedError, "Must be Implemented in child classes"

    def kill(  self , number ):
        """
        kill the Job
        @param execution_config: a configuration object for this execution system
        @type execution_config: an ExecutionConfig subclass instance
        @param number:
        @type number:
        abstract method. this method must be implemented in child classes
        """
        raise NotImplementedError, "Must be Implemented in child classes"
            



    def _logError( self , dirPath , serviceName , jobKey , userMsg = None , logMsg = None ):


        if userMsg :
            self.status_manager.setStatus( dirPath, Status( code = 5 , message = userMsg ) )

        if logMsg :
            _log.error( "%s/%s : %s" %( serviceName ,
                                        jobKey ,
                                        logMsg
                                      )
                        )
          
          
          
          
