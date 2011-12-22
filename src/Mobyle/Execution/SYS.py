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
from subprocess import Popen
from signal import SIG_DFL , SIGTERM , SIGKILL
from time import sleep

from logging import getLogger
_log = getLogger(__name__)

from Mobyle.Admin import Admin
from Mobyle.Status import Status
from Mobyle.Execution.ExecutionSystem import ExecutionSystem
from Mobyle.MobyleError import MobyleError

__extra_epydoc_fields__ = [('call', 'Called by','Called by')]



class SYS(ExecutionSystem):
    """
    Run the commandline by a system call
    """

    def _run(self , commandLine , dirPath , serviceName , jobKey , jobState , queue , xmlEnv ):
        """
        Run the commandLine in a subshell (system call) and redirect the standard error and output on service.name.out and service.name.err, then restore the sys.stderr and sys.stdout
        @return: the L{Status} of this job and a message
        @rtype: Status object
        """
        fout = open( serviceName + ".out" , 'w' )
        ferr = open( serviceName + ".err" , 'w' )

        try:
            #the new process launch by popen must be a session leader 
            # because it launch in background and if we send a siggnal to the shell 
            # this signal will no propagate to all child process
            # and if we kill the process leader we kill the python 
            # thus we execute our setsid which transform the new process as a session leader
            # and execute the command prior to return.
            # in these conditions we could kill the process leader and the signal is propagate to
            # all processes belonging to this session. 

            setsidPath = '%s/Tools/setsid' %self._cfg.mobylehome()
            command = [ setsidPath , setsidPath , '/bin/sh' , '-c' , commandLine ]
            # _log.debug("SYS env : %s\n" % str(self.xmlEnv) )

            pipe = Popen( command ,
                          shell     = False ,
                          stdout    = fout ,
                          stdin     = None ,
                          stderr    = ferr ,
                          close_fds = True ,
                          env       = xmlEnv
                          )

        except OSError, err:
            msg= "System execution failed: command = %s : %s" %( command , err)
            self._logError( dirPath , serviceName , jobKey,
                            admMsg = msg ,
                            userMsg = "Mobyle internal server error" ,
                            logMsg = None )
            
            _log.critical( "%s/%s : %s" %( serviceName ,
                                           jobKey ,
                                           msg
                                           ) ,
                                            exc_info = True
                             )

            raise MobyleError , msg 
            
        jobPid = pipe.pid
        
        adm = Admin( dirPath )
        adm.setExecutionAlias( self.execution_config_alias )
        adm.setNumber( jobPid )
        adm.commit()

        linkName = ( "%s/%s.%s" %( self._cfg.admindir() ,
                                   serviceName ,
                                   jobKey
                                )
                     )
        try:
            os.symlink(
                os.path.join( dirPath , '.admin') ,
                linkName
                )
        except OSError , err:
            msg = "can't create symbolic link %s in ADMINDIR: %s" %( linkName , err )
            self._logError( dirPath , serviceName , jobKey,
                            userMsg = "Mobyle internal server error" ,
                            logMsg = None )
            
            _log.critical( "%s/%s : %s" %( serviceName ,
                                           jobKey ,
                                           msg
                                            )
                             )
            raise MobyleError , msg
        pipe.wait()

        try:
            os.unlink( linkName )
        except OSError , err:
            msg = "can't remove symbolic link %s in ADMINDIR: %s" %( linkName , err )

            self._logError( dirPath , serviceName , jobKey ,
                            userMsg = "Mobyle internal server error" ,
                            logMsg = None )
            
            _log.critical( "%s/%s : %s" %( serviceName ,
                                           jobKey,
                                           msg
                                        )
                             )

            raise MobyleError , msg
        fout.close()
        ferr.close()
        #self._returncode = pipe.returncode
        
        oldStatus = self.status_manager.getStatus( dirPath )
        if oldStatus.isEnded():
            return oldStatus
        else:
            if pipe.returncode == 0 :# finished
                status = Status( code = 4 ) #finished
            elif pipe.returncode == -15 or pipe.returncode == -9: #killed
                status = Status( code = 6 , message = "Your job has been cancelled" ) 
            elif pipe.returncode < 0 or pipe.returncode > 128:
                #all the signals that we don't know where they come from
                status = Status( code = 5 , message = "Your job execution failed ( %s )" %pipe.returncode )
            else:
                status = Status( code= 4 , message = "Your job finished with an unusual status code ( %s ), check your results carefully." % pipe.returncode )
            return status
    

    def getStatus( self , pid ):
        """
        @param pid:
        @type pid:
        @return: the status of job with pid pid
        @rtype: a Status instance
        """
        pid = int( pid )
        try:
            message = None
            os.kill( pid , SIG_DFL )
        except OSError , err:
            if str( err ).find( 'No such process' ) != -1:
                return Status( code = -1 ) #unknown
            else:
                raise MobyleError( str(err) ) 
        return Status( code = 3 , message = message ) #running

    def kill( self, job_pid ):
        """
        kill a job
        @param job_pid: the pid of the job
        @type job_pid: int
        @raise MobyleError: if can't kill the job
        @call: by L{Utils.Mkill}
        """
        try:
            job_pid = int( job_pid )
            job_pgid = os.getpgid( job_pid )
        except ValueError, err:
            raise MobyleError( "can't kill job  - %s" % err )
        try:
            os.killpg( job_pgid , SIGTERM )
        except OSError , err:
            raise MobyleError( "can't kill job  - %s" % err )
        try:
            sleep(0.2)
            os.killpg( job_pgid , SIG_DFL )
            try:
                os.killpg( job_pgid , SIGKILL )
            except OSError , err:
                raise MobyleError , "can't kill job - %s" % err
        except OSError , err:
            return None
