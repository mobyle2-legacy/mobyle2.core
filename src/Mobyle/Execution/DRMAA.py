
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
import imp
from logging import getLogger
_log = getLogger(__name__)

from Mobyle.Status import Status
from Mobyle.Admin import Admin
from Mobyle.Execution.ExecutionSystem import ExecutionSystem 

from Mobyle.MobyleError import MobyleError

__extra_epydoc_fields__ = [('call', 'Called by','Called by')]




class DRMAA(ExecutionSystem):
    """
    Run the commandline with batch system DRMAA bindings
    """
    def __init__( self, drmaa_config ):
        super( DRMAA , self ).__init__( drmaa_config )
        self.drmaa_library_path = drmaa_config.drmaa_library_path
        os.environ[ 'DRMAA_LIBRARY_PATH'] = self.drmaa_library_path
        fp , pathname , description = imp.find_module("drmaa")
        self.drmaa = imp.load_module( "drmaa" , fp , pathname , description )
        self.contactString = drmaa_config.contactString
        
    def _drmaaStatus2mobyleStatus( self , drmaaStatus ):
        if drmaaStatus == self.drmaa.JobState.RUNNING:
            return Status( 3 ) #running
        elif drmaaStatus == self.drmaa.JobState.UNDETERMINED:
            return Status( -1 ) #unknown
        elif drmaaStatus == self.drmaa.JobState.QUEUED_ACTIVE:
            return Status( 2 ) #pending
        elif drmaaStatus == self.drmaa.JobState.DONE:
            return Status( 4 ) #finished
        elif drmaaStatus == self.drmaa.JobState.FAILED:
            return Status( 5 ) # error
        elif drmaaStatus == self.drmaa.JobState.SYSTEM_ON_HOLD:
            return Status( 7 ) # hold
        elif drmaaStatus == self.drmaa.JobState.USER_ON_HOLD:
            return Status( 7 ) # hold
        elif drmaaStatus == self.drmaa.JobState.USER_SYSTEM_ON_HOLD:
            return Status( 7 ) # hold
        elif drmaaStatus == self.drmaa.JobState.SYSTEM_SUSPENDED:
            return Status( 7 ) # hold
        elif drmaaStatus == self.drmaa.JobState.USER_SUSPENDED:
            return Status( 7 ) # hold
        elif drmaaStatus == self.drmaa.JobState.USER_SYSTEM_SUSPENDED:
            return Status( 7 ) # hold
        else:
            return Status( -1 )


    def _run( self , commandLine , dirPath , serviceName , jobKey , jobState , queue , xmlEnv ):
        """
        Run the commandLine 
        redirect the standard error and output on service.name.out and service.name.err, then restore the sys.stderr and sys.stdout
        @param execution_config: a configuration object for this execution system
        @type execution_config: a L{DRMAAConfig}  instance
        @return: the L{Status} of this job and a message
        @rtype: Status
        """
        
        if (os.getcwd() != os.path.abspath(dirPath) ):
            msg = "the process is not in the working directory"

            self._logError( dirPath , serviceName , jobKey ,
                            userMsg = "Mobyle internal server error" ,
                            logMsg = msg )

            raise MobyleError , msg

        else:
            fout = open( serviceName + ".out" , 'w' )
            ferr = open( serviceName + ".err" , 'w' )
            try:
                drmaaSession = self.drmaa.Session( contactString = self.contactString )
                try:
                    drmaaSession.initialize()
                except self.drmaa.errors.AlreadyActiveSessionException:
                    pass
                except Exception, err:
                    self._logError( dirPath , serviceName , jobKey ,
                                    userMsg = "Mobyle internal server error" ,
                                    logMsg = None )
                    _log.critical( "error during drmaa intitialization for job %s/%s: %s" %(serviceName, jobKey , err) ,  exc_info= True )
            
                jt = drmaaSession.createJobTemplate()
                jt.workingDirectory = dirPath
                jt.jobName = jobKey
                jt.outputPath = ":" + os.path.join( dirPath , fout.name )
                jt.errorPath  = ":" + os.path.join( dirPath , ferr.name )
                jt.joinFiles = False
                jt.jobEnvironment = xmlEnv
                jt.remoteCommand = "sh"
                jt.args = [ os.path.join( dirPath , ".command" ) ]
                nativeSpecification = ''
                if self.execution_config.nativeSpecification:
                    nativeSpecification = self.execution_config.nativeSpecification
                elif queue:
                    nativeSpecification = "%s -q %s" % ( nativeSpecification , queue )
                if nativeSpecification:
                    jt.nativeSpecification = nativeSpecification
                jt.blockEmail = True
                drmJobid = drmaaSession.runJob( jt )
            except self.drmaa.errors , err :
                _log.error( "cannot exit from drmaa properly try to deleting JobTemplate: " + str( err ) )
                try:
                    drmaaSession.deleteJobTemplate( jt )
                    drmaaSession.exit()
                except Exception , err :
                    _log.error( "cannot exit from drmaa properly : " + str( err ) )
               
                msg= "System execution failed: " +str( err ) 
                self._logError( dirPath , serviceName , jobKey ,
                                userMsg = "Mobyle internal server error" ,
                                logMsg = None )
                
                _log.critical( "%s/%s : %s" %( serviceName ,
                                                   jobKey ,
                                                   msg
                                                   )
                                 )

                raise MobyleError , msg 
            except  Exception , err :
                _log.debug( "an error occured in drmaa.run method : %s" %err )
                raise MobyleError( "Internal Server Error")
                    
            adm = Admin( dirPath )
            adm.setExecutionAlias( self.execution_config_alias ) 
            adm.setNumber( drmJobid ) 
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
                try:
                    drmaaSession.deleteJobTemplate( jt )
                    drmaaSession.exit()
                except Exception , err :
                    _log.error( "cannot exit from drmaa properly : " + str( err ) )
                    
                msg = "can't create symbolic link %s in ADMINDIR: %s" %( linkName , err )

                self._logError( dirPath , serviceName , jobKey ,
                                userMsg = "Mobyle internal server error" ,
                                logMsg = None )
                
                _log.critical( "%s/%s : %s" %( serviceName ,
                                               jobKey ,
                                               msg
                                            )
                                 )

                raise MobyleError , msg
                        
            #JobInfo =( jobId , hasExited , hasSignal , terminatedSignal, hasCoreDump, wasAborted, exitStatus, resourceUsage)
            #            0          1          2              3               4            5           6           7
            try:
                jobInfos = drmaaSession.wait( drmJobid , self.drmaa.Session.TIMEOUT_WAIT_FOREVER )
            except self.drmaa.errors , err :
                try:
                    drmaaSession.deleteJobTemplate( jt )
                    drmaaSession.exit()
                except Exception , err :
                    _log.error( "cannot exit from drmaa properly : " + str( err ) )
                
                self._logError( dirPath , serviceName , jobKey ,
                                userMsg = "Mobyle internal server error" ,
                                logMsg = None )
                
                _log.critical( "%s/%s : %s" %( serviceName ,
                                               jobKey ,
                                               "cannot wait the completion of job : %s" % err
                                            )
                                 )

            try:
                os.unlink( linkName )
            except OSError , err:
                try:
                    drmaaSession.deleteJobTemplate( jt )
                    drmaaSession.exit()
                except Exception , err :
                    _log.error( "cannot exit from drmaa properly : " + str( err ) )
                    
                msg = "cannot remove symbolic link %s in ADMINDIR: %s" %( linkName , err )

                self._logError( dirPath , serviceName , jobKey ,
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
            
            oldStatus = self.status_manager.getStatus( dirPath )
            
            if oldStatus.isEnded():
                status= oldStatus
            else:
                if jobInfos[ 5 ] :#wasAborted
                    status = Status( code = 6 , message = "Your job has been cancelled" ) #killed
                else:
                    if jobInfos[ 1 ]:#hasExited
                        if jobInfos[ 6 ] == 0:#exitStatus
                            status = Status( code = 4 ) #finished
                        else:
                            status = Status( code = 4 , message = "Your job finished with an unusual status code ( %d ), check your results carefully." % jobInfos[ 6 ] )
                    else:
                        status = Status( code = 6 , message = "Your job execution failed ( %d )" %jobInfos[ 6 ] ) 

            try:
                drmaaSession.deleteJobTemplate( jt )
                drmaaSession.exit()
            except :
                _log.error( "cannot exit from drmaa properly" )
            
            return status
        

    def getStatus( self , key ):
        """
        @param execution_config: a configuration object for this execution system
        @type execution_config: a L{DRMAAConfig}  instance
        @param key: the value associate to the key "NUMBER" in Admin object (and .admin file )
        @type key: string
        @return: the status of the job corresponding to the key 
        @rtype: Status instance
        @call: by L{Utils.getStatus}
        """
        try:
            s = self.drmaa.Session( contactString = self.contactString )
        except Exception , err:
            _log.error( "getStatus(%s) cannot open drmma session : %s " %( key , err ) )
            return Status( -1 ) #unknown 
        try:
            s.initialize()
        except self.drmaa.errors.AlreadyActiveSessionException:
            pass
        except Exception, err:
            _log.critical( "error during drmaa intitialization for job %s: %s" %(key , err) ,  exc_info= True )
            
        try:
            drmaaStatus = s.jobStatus( key )
        except :
            s.exit()
            return Status( -1 ) #unknown 
        s.exit()
        return self._drmaaStatus2mobyleStatus( drmaaStatus ) 


    def kill( self , key ):
        """
        kill a job
        @param execution_config: a configuration object for this execution system
        @type execution_config: a L{DRMAAConfig}  instance
        @param key : the value associate to the key "NUMBER" in Admin object (and .admin file )
        @type key: string
        @raise MobyleError: if can't kill the job
        @call: by L{Utils.Mkill}
        """
        try:
            s = self.drmaa.Session( contactString = self.contactString )
        except Exception , err:
            _log.error( "kill( %s ) cannot open drmma session : %s " %( key , err ) )
            return
        try:
            s.initialize()
        except self.drmaa.errors.AlreadyActiveSessionException:
            pass
        except Exception, err:
            _log.critical( "error during drmaa intitialization for job %s: %s" %(key , err) ,  exc_info= True )
            
        try:
            s.control( key , self.drmaa.JobControlAction.TERMINATE )
        except Exception , err :
            msg = "error when trying to kill job %s : %s" %( key , err )
            _log.error( msg )
            raise MobyleError( msg )
        finally:    
            s.exit()
        return

