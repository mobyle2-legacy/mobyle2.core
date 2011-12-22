
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

import logging
_log = logging.getLogger(__name__)

from Mobyle.Execution.ExecutionSystem import ExecutionSystem 
from Mobyle.MobyleError import MobyleError
from Mobyle.Admin import Admin
from Mobyle.Status import Status
from Mobyle.ConfigManager import Config
_cfg = Config()
__extra_epydoc_fields__ = [('call', 'Called by','Called by')]


class Dummy(ExecutionSystem):
    """
    Run the commandline by ???
    """

    def run(self, commandLine , dirPath , serviceName , jobKey , jobState , queue , xmlEnv ):
        """
        Run the commandLine 
        redirect the standard error and output on service.name.out and service.name.err, then restore the sys.stderr and sys.stdout
        @return: the L{Mobyle.Status.Status} of this job and a message
        @rtype: Status  object
        """
        jobKey = self.getKey()
        fout = open( serviceName + ".out" , 'w' )
        ferr = open( serviceName + ".err" , 'w' )

        try:
            ## execute the commandline through your favorite execution system
            pass
        except OSError, err:
            msg= "System execution failed: " + str(err)
            self._logError( dirPath , serviceName ,jobKey,
                            userMsg = "Mobyle internal server error" ,
                            logMsg = None )
                
            _log.critical( "%s/%s : %s" %( self.serviceName ,
                                                jobKey ,
                                                msg
                                                )
                                )

            raise MobyleError , msg 
                
            adm = Admin( dirPath )
            adm.setExecutionAlias( self.execution_config_alias )  ## store the alias of execution config used for this job 
            adm.setNumber( jobKey ) ## store the key to query/retrieve this job on this system execution
            adm.commit()

            ## link the .admin file in ADMINDIR which looklike to a "process table"
            linkName = ( "%s/%s.%s" %(self. _cfg.admindir() ,
                                      serviceName ,
                                      jobKey
                                    )
                         )
            
            try:
                os.symlink(
                    os.path.join( self.dirPath , '.admin') ,
                    linkName
                    )
            except OSError , err:
                msg = "can't create symbolic link %s in ADMINDIR: %s" %( linkName , err )
                self._logError( dirPath , serviceName ,jobKey,
                                userMsg = "Mobyle internal server error" ,
                                logMsg = None )
                
                _log.critical( "%s/%s : %s" %( serviceName ,
                                               jobKey ,
                                               msg
                                            )
                                 )
                raise MobyleError , msg

            
            ## wait the completion of the job 
            ## THIS CLASS MUST BE SYNCHRON WITH THE JOB  
            

            try:
                ## remove the job from the ADMINDIR ( "process table" )
                os.unlink( linkName )
            except OSError , err:
                msg = "can't remove symbolic link %s in ADMINDIR: %s" %( linkName , err )
                self._logError( dirPath , serviceName ,jobKey,
                                userMsg = "Mobyle internal server error" ,
                                logMsg = None )
                
                _log.critical( "%s/%s : %s" %( self.serviceName ,
                                                jobKey ,
                                                msg
                                                )
                                 )
                raise MobyleError , msg
            ##close the standard output and standard error file
            fout.close()
            ferr.close()
            
            oldStatus = self.status_manager.getStatus( dirPath )
 
            #if the oldStatus is terminal ( finish error killed )
            #I don't modify this status 
            if oldStatus.isEnded():
                return oldStatus
            else:
                ## analyse the returncode of the job
                ## and instanciate a Status according the returncode
                ## then return the Status
                status = Status( code = 4 ) #finished
            return status
        

    def getStatus( self , key ):
        """
        @param key: the value associate to the key "NUMBER" in Admin object (and .admin file )
        @type key: string
        @return: the status of the job corresponding to the key 
        @rtype: Mobyle.Status.Status instance
        @call: by L{Utils.getStatus}
        """
        ##query your execution system about the job with this key
        ##translate the answer in mobyle compliant status and message
        
        ## for mobyle status see Mobyle.Status.Status
        mobyle_status_code = 3 # running
        message = "my job is running"
        return Status( code = mobyle_status_code , message = message )


    def kill( self , key ):
        """
        kill a job
        @param key : the value associate to the key "NUMBER" in Admin object (and .admin file )
        @type key: string
        @raise MobyleError: if can't kill the job
        @call: by L{Utils.Mkill}
        """
        return None
        
