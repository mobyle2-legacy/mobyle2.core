########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

"""
Run the command , do the choice of a synchronous vs. asynchronous process.
in the case of asynchronous process, manage the creation of the child process and the synchronization with it.
"""


import os
import sys
import time
import cPickle

from logging import getLogger , shutdown as logging_shutdown
rf_log = getLogger( __name__ )

from Mobyle.CommandBuilder  import CommandBuilder
from Mobyle.JobState  import JobState
from Mobyle.Status import Status
from Mobyle.StatusManager import StatusManager
from Mobyle.Admin import Admin
from Mobyle.MobyleError import MobyleError

__extra_epydoc_fields__ = [ ('call', 'Calledby','Called by') ]



class CommandRunner:
    """

    """

    def __init__( self, job , jobState = None  ):
        """
        instanciate a L{CommandBuilder} and use it to build the CommandLine, then run it
        @param service:
        @type job: a L{Job} instance
        @param jobState:
        @type jobState:
        @call: l{Job.run}
        @todo: implementation pour le warper de cgi ou WS a faire
        """
        self.job = job
        self.job_dir = self.job.getDir()
        self._service = self.job.getService()
        if jobState is None:
            self._jobState = JobState( self.job_dir )
        else:
            self._jobState = jobState
        
        commandBuilder = CommandBuilder()
        
        method = self._service.getCommand()[1].upper()

        if method == '' or method == 'LOCAL':

            try:
                cmd = commandBuilder.buildLocalCommand( self._service )
                self._commandLine = cmd[ 'cmd' ]
                self._xmlEnv = cmd[ 'env' ]
                paramfiles = cmd[ 'paramfiles' ]
            except Exception ,err :
                msg = "an error occured during the command line building: " 
                self._logError( userMsg = "Mobyle Internal Server Error",
                                logMsg = None #the error log is filled by the rf_log.critical
                                )
                #this error is already log in build.log
                msg = "%s/%s : %s" %( self._service.getName() ,
                                                   self.job.getKey() , 
                                                   msg , 
                                                   )
                
                if self.job.cfg.debug( self._service.getName() ) == 0:
                    rf_log.critical( msg  , exc_info = True) # send an email
                else:
                    rf_log.error( msg , exc_info = True) 
                 
                raise MobyleError , "Mobyle Internal Server Error"
            js_paramfiles = []
            if paramfiles :
                for paramfile_name , string_handle  in paramfiles.items():
                    paramfile_handle = open( os.path.join(  self.job_dir , paramfile_name ) , 'w' )
                    content = string_handle.getvalue()
                    paramfile_handle.write( content )
                    paramfile_handle.close()
                    js_paramfiles.append( ( os.path.basename( paramfile_name ) , len( content ) ) )
                self._jobState.setParamfiles( js_paramfiles )
                self._jobState.commit()
                
        elif method == "GET" or method == "POST" or method == "POSTM":
            raise NotImplementedError ,"cgi wrapping is not yet implemented"
        elif method == "SOAP" or method == "XML-RPC":
            raise NotImplementedError ,"cgi wrapping is not yet implemented"
        else:
            raise MobyleError, "unknown method of command : "+str( method )
        
        try:
            commandFile = open( os.path.join( self.job_dir , ".command" ), 'w' )
            commandFile.write( self._commandLine + "\n" )
            commandFile.close()
        except IOError , err:
            msg = "an error occured during the .command file creation: " + str( err )
            self._logError( userMsg= "Mobyle Internal Server error" ,
                            logMsg = msg
                            )
            raise MobyleError , err

        self._jobState.setCommandLine( self._commandLine )
        self._jobState.commit()


    def run(self):
        """
        instanciate  an L{AsynchronRunner} in function of the attribute synchron.
        """
        return AsynchronRunner( self._commandLine , self.job_dir , self.job , jobState = self._jobState , xmlEnv = self._xmlEnv )

    def getCmdLine(self):
        return self._commandLine


    def _logError( self , userMsg = None , logMsg = None ):

        
        if userMsg :
            sm = StatusManager()
            sm.setStatus( self.job_dir , Status( code = 5 , message = userMsg ) )

        if logMsg :
            rf_log.error( "%s/%s : %s" %( self._service.getName() ,
                                          self.job.getKey() ,
                                          logMsg
                                          )
                          )



class AsynchronRunner:
    """
    manage the child process creation
    manage the synchronisation with his child
    """
    

    def __init__( self, commandLine , work_dir , job , jobState = None , cfg = None , xmlEnv = None ):
        """
        the father process
        @param commandLine: the command to be executed
        @type commandLine: String
        @param work_dir: the absolute path to directory where the job will be executed
        @type work_dir: String
        @param service:
        @type service: A L{Service} instance
        @param jobState:
        @type jobState: a L{JobState} instance
        @type cfg: L{ConfigManager.Config} instance
        @call: L{CommandRunner.run}
        """
        if cfg :
            self._cfg = cfg
        else:
            from Mobyle.ConfigManager import Config
            self._cfg = Config()

        self._command = commandLine
        self._xmlEnv = xmlEnv
        self.work_dir = work_dir
        self._job = job
        self._service = self._job.getService()
        self._child_pid = 0
        #self.child_done = False

        if jobState is None:
            self.jobState = JobState( self.work_dir )
        else:
            self.jobState = jobState
        try:
            self._child_pid = os.fork()
        except Exception , err:
            msg = "Can't fork : " + str( err )
            self._logError( logMsg = msg ,
                            userMsg = "Mobyle Internal server error"
                            )

            raise MobyleError , msg
        
        
        if self._child_pid > 0 : ####### FATHER #######
            pass    
        elif self._child_pid == 0 : ####### CHILD #######
            os.setsid()
            devnull = os.open( "/dev/null" , os.O_RDWR )
            os.dup2( devnull , sys.stdin.fileno() )

            try:    
                os.chdir( self.work_dir )
            except OSError, err:
                msg = "unable to change directory to:" + str( err )
                self._logError( logMsg = None ,
                                userMsg = "Mobyle Internal server error"
                                )
                rf_log.critical( msg )
                raise MobyleError , "Internal server Error"

            serviceName = self._service.getName()
            
            try:
                #logfile = os.open(  os.path.join( self._cfg.log_dir(), 'debug' ) , os.O_CREAT | os.O_WRONLY | os.O_TRUNC )    
                logfile = os.open( os.path.join( self._cfg.log_dir(), 'child_log' ) , os.O_APPEND | os.O_WRONLY | os.O_CREAT , 0664 )                
                            
                os.dup2( logfile , sys.stdout.fileno() )
                os.dup2( logfile , sys.stderr.fileno() )
                os.close( logfile )

                
            except ( IOError , OSError ) , err :
                rf_log.critical( "error in redirecting stderr or stdout to debug : ", exc_info = True ) 
                
                self._logError( logMsg = None ,
                                userMsg = "Mobyle Internal server error"
                                )
                
                try :
                    os.dup2( devnull , sys.stdout.fileno() )
                    os.dup2( devnull , sys.stderr.fileno() )
                except (IOError , OSError ) , err:
                    rf_log.critical( "error in redirecting stderr or stdout to /dev/null : " , exc_info = True ) 
                    
                
            childName = os.path.join( self._cfg.mobylehome() ,  
                                      'Src' ,
                                      'Mobyle' ,
                                      'RunnerChild.py'
                                      )


            email = self._job.getEmail()
            
            if email is None:
                email_to = None
            else:
                email_to = str( email )

            try:
                paramsOut = self._service.getAllOutParameter(  )
                results_mask ={}
                evaluator = self._service.getEvaluator()
                stdout = False
                for paramName in paramsOut :
                    if self._service.precondHas_proglang( paramName , 'python' ):
                        preconds = self._service.getPreconds( paramName , proglang='python' )
                        allPrecondTrue = True
                        for precond in preconds:
                            if not evaluator.eval( precond ) :
                                allPrecondTrue = False
                                break
                        if not allPrecondTrue :
                            continue #next parameter
                    if self._service.isstdout( paramName ):
                        stdout = True

                    unixMasks = self._service.getFilenames( paramName , proglang = 'python' )
                    results_mask [ paramName ] = unixMasks 
                serviceName = self._service.getName()
                
                if not stdout :
                    results_mask [ 'stdout' ] =  [ serviceName + '.out' ]
                results_mask [ 'stderr' ] = [ serviceName + '.err']
            
            except MobyleError, err:
                msg = "AsynchronRunner.__init__ : " + str( err )
                self._logError( logMsg = msg ,
                                userMsg = "Mobyle Internal server error"
                                )
                raise MobyleError , msg
                
            forChild = { 'serviceName' : self._service.getName() ,
                         'email'       : email_to ,
                         'dirPath'     : self.work_dir,
                         'commandLine' : self._command ,
                         'resultsMask' : results_mask ,
                         'xmlEnv'      : self._xmlEnv ,
                         'email_notify': self._job.email_notify
                         }
            try:
                fh = open( os.path.join( self.work_dir , ".forChild.dump") ,'w' )
                cPickle.dump( forChild , fh )
                fh.close()
            except IOError , err:
                msg = "error during dumping forChild.dump of job %s" %self.work_dir
                self._logError( logMsg = msg ,
                                userMsg = "Mobyle Internal server error"
                                )
            
            cmd = [ childName ]
            
            logging_shutdown() #close all loggers
            try:
                os.execv( cmd[0] , cmd )
            except Exception, err:
                msg = "AsynchronRunner : CRITICAL : L 420 : %s : %s/%s : __init__: exec child caught an error: %s" %( time.strftime( '%a, %d %b %Y %H:%M:%S' , time.localtime() ) ,
                                                                                                           self._service.getName() ,
                                                                                                           self._job.getKey() ,
                                                                                                           err
                                                                                                           )
                try:
                    mylog = open( os.path.join( self._cfg.log_dir() , 'error_log' ) , 'a' )
                except:
                    mylog = open( '/dev/null' )
                mylog.write( msg +'\n')
                mylog.close()
                self._logError( logMsg = None ,
                                userMsg = "Mobyle Internal server error"
                                )
                raise MobyleError, msg


    def _logError( self , userMsg = None , logMsg = None ):

        if userMsg :
            sm = StatusManager()
            sm.setStatus( self.work_dir , Status( code = 5 , message =  userMsg ) )
            

        if logMsg :
            rf_log.error( "%s/%s : %s" %( self._service.getName() ,
                                          self._job.getKey() ,
                                          logMsg
                                          )
                        )
    


