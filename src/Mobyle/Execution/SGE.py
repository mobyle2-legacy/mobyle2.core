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
from subprocess import Popen, PIPE

from logging import getLogger
_log = getLogger(__name__)

from Mobyle.Admin import Admin
from Mobyle.Execution.ExecutionSystem import ExecutionSystem 
from Mobyle.MobyleError import MobyleError
from Mobyle.Status import Status

__extra_epydoc_fields__ = [('call', 'Called by','Called by')]

        
                
class SGE (ExecutionSystem):
    """
    Run the commandline with Sun GridEngine commands
    """
        
    def __init__( self, sge_config ):
        super( SGE , self ).__init__( sge_config )
        arch_path= os.path.join( sge_config.root , 'util' , 'arch' )
        try:
            arch_pipe = Popen(arch_path         ,
                              shell     = False ,
                              stdout    = PIPE  ,
                              stdin     = None  ,
                              stderr    = None  ,
                              close_fds = True  )
            arch_pipe.wait() 
            arch_rc = arch_pipe.returncode
        except OSError , err:
            #this error is log by calling method because I can't access to jobKey , adm status ... from static method
            msg = "SGE: I can't determined the system arch:"+str(err)
            raise MobyleError( msg )
        if arch_rc != 0 :
            msg = "I can't determined the system arch (return code = " + str( arch_rc ) + " )"
            raise MobyleError( msg )
        
        arch = ''.join( arch_pipe.stdout.readlines() ).strip()

        self.sge_prefix = os.path.join( sge_config.root , 'bin' , arch )
        self.sge_env = {'SGE_CELL': sge_config.cell , 'SGE_ROOT': sge_config.root }   


    def _run( self , commandLine , dirPath , serviceName , jobKey , jobState , queue , xmlEnv ):
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
        
        options = { '-cwd': ''           ,  #set the working dir to current dir
                    '-now': 'n'          ,  #the job is not executed immediately
                    '-N' : jobKey        ,  #the id of the job
                    '-V' : ''               #job inherits of the whole environment
                    }
        if queue:
            options[ '-q' ] = queue
        sge_opts = ''

        for opt in options.keys():
            sge_opts += opt + ' ' + options[opt]+' '
                 
        sge_cmd = os.path.join( self.sge_prefix , 'qrsh' ) + ' ' + sge_opts
        cmd = sge_cmd + " " + commandLine

        try:
            fout = open( serviceName + ".out" , 'w' )
            ferr = open( serviceName + ".err" , 'w' )
        except IOError , err:
            msg= "SGE: can't open file for standard job output: "+ str(err)
            self._logError( dirPath , serviceName , jobKey ,
                            admMsg = msg ,
                            userMsg = "Mobyle internal server error" ,
                            logMsg = msg )

            raise MobyleError , msg
        xmlEnv.update( self.sge_env )
        try:
            pipe = Popen( cmd ,
                          shell  = True ,
                          stdout = fout  ,
                          stdin  = None  ,
                          stderr = ferr  ,
                          close_fds = True ,
                          env       = xmlEnv
                          )
        except OSError, err:
            msg= "SGE execution failed: "+ str(err)
            self._logError( dirPath , serviceName , jobKey ,
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
        adm = Admin( dirPath )
        adm.setExecutionAlias( self.execution_config_alias  )
        adm.setNumber( jobKey )
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
            self._logError( dirPath , serviceName , jobKey ,
                            admMsg = msg ,
                            userMsg = "Mobyle internal server error" ,
                            logMsg = None )
            _log.critical( "%s/%s : %s" %( serviceName ,
                                           jobKey  ,
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
                            admMsg = msg ,
                            userMsg = "Mobyle internal server error" ,
                            logMsg = None )
            _log.critical( "%s/%s : %s" %( serviceName ,
                                           jobKey ,
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
            elif pipe.returncode in ( 137 , 143 , 153 ): #killed
                ## 137 =  9 ( SIGKILL ) + 128 ( python add 128 )
                ## 143 = 15 ( SIGTERM )
                ## 153 = 25 ( SIGXFSZ ) + 128 (file size exceeded )
                ## be careful if a job exit with a 137 or 153 exit status it will be labelled as killed
                status = Status( code = 6 , message = "Your job has been cancelled" ) 
            elif pipe.returncode > 128 :
                status = Status( code = 6 , message = "Your job execution failed ( %s )" %pipe.returncode ) 
                ## if return code > 128 it's a signal
                ## the 9 , 15 25 signal are send by administrator
                ## the other are self aborting signal see signal(7)   
            else:
                status = Status( code = 4 , message = "Your job finished with an unusual status code ( %s ), check your results carefully." % pipe.returncode )
            return status


    def getStatus( self ,jobNum ):
        """
        @param sge_config: the configuration of this Execution engine
        @type sge_config: a L{SGEConfig} instance
        @param jobNum:
        @type jobNum:
        @return: the status of job with number jobNum
        @rtype: a Mobyle.Status.Status instance
        @todo: for best performance, restrict the sge querying to one queue
        """
        sge_cmd = [ os.path.join( self.sge_prefix , 'qstat' ) , '-r' ]
        
        try:
            pipe = Popen( sge_cmd,
                          executable = sge_cmd[0] ,
                          shell = False ,
                          stdout = PIPE ,
                          stdin = None  ,
                          stderr= None  ,
                          close_fds = True ,
                          env= self.sge_env
                          )
        except OSError , err:
            raise MobyleError , "can't querying sge : %s :%s "%( sge_cmd , err )

        sge2mobyleStatus = { 'r' : 3 , # running
                             't' : 3 ,
                             'R' : 3 ,
                             's' : 7 , #hold
                             'S' : 7 , 
                             'T' : 7 ,
                             'h' : 7 ,
                             'w' : 2 , #pending
                             'd' : 6 , #killed 
                             'E' : 5 , #error
                             }

        for job in pipe.stdout :
            
            job_sge_status = job.split()
            try:
                status = job_sge_status[ 4 ][ -1 ]
                continue
            except ( ValueError , IndexError ):
                pass #it's not the fisrt line
            try:
                if not ( jobNum == job_sge_status[2] and 'Full' == job_sge_status[0] ):
                    continue #it's not the right jobNum
            except IndexError :
                continue #it's not the 2nde line

            pipe.stdout.close()
            pipe.wait()
            
            if pipe.returncode == 0 :
                try:
                    return Status( code = sge2mobyleStatus[ status ]  )
                except MobyleError , err :
                    raise MobyleError , "unexpected sge status: " +str( status )
            else:
                raise MobyleError , "cannot get status " + str( pipe.returncode )
        return Status( code = -1 ) #unknown

        
    def kill( self, job_number ):
        """
        @todo: kill the Job
        """
        sge_cmd = "%s %s 1>&2" %( os.path.join( self.sge_prefix , 'qdel' ) ,  job_number )
        os.environ.update( self.sge_env )
        os.system( sge_cmd )
        

