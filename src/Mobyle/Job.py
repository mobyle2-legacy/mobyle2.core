########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.        #
#                                                                                      #
########################################################################################

import os 
import random 
from string import ascii_uppercase
import resource
from hashlib import md5
import time 
import glob
import logging 
j_log = logging.getLogger( __name__ )

from Mobyle.JobState import JobState , path2url , url2path
from Mobyle.Admin import Admin
from Mobyle.Status import Status
from Mobyle.StatusManager import StatusManager
from Mobyle.MobyleError import MobyleError , UserValueError
from Mobyle.Utils import executionLoader

__extra_epydoc_fields__ = [('call', 'Called by','Called by')]



class Job:

    """
    create the environment to run a job
      - working directory creation
    """
    
    def __init__(self, service=None , cfg=None , session = None , userEmail = None , workflowID = None , email_notify= 'auto' , ID = None ):
        """
        @param service:
        @type service: a {Service} instance
        @param cfg: a config object
        @type cfg: L{ConfigManager.Config} instance
        @param session:
        @type session: a L{Session} instance
        @param userEmail: the email of the user 
        @type userEmail: a L{Mobyle.Net.EmailAddress} instance
        @param workflowID: the url of the workflow owner of this job
        @type workflowID: string
        @param email_notify: if the user must be or not notify of the results at the end of the Job.
        the 3 authorized values for this argument are: 
          - 'true' to notify the results to the user
          - 'false' to Not notify the results to the user
          - 'auto' to notify the results based on the job elapsed time and the config  EMAIL_DELAY
        @type email_notify: string 
        """
        
        if cfg:
            self.cfg = cfg
        else:
            from Mobyle.ConfigManager import Config
            self.cfg = Config()
        self.runner = None
        self.session = session
        self.userEmail = userEmail
        self.workflowID = workflowID
        self.sm = StatusManager()
        if ID:
            self.ID = ID
            self.work_dir = url2path( ID )
            self.jobState = JobState( uri = ID )
            self.key = os.path.split( self.work_dir )[ 1 ]
        else:
            self.service = service
            self.work_dir = None
            self.jobState = None
            self.key = self._newKey()
            self.email_notify = email_notify
            self.makeEnv()
            self.ID = self.getURL()

    def makeEnv( self, uri = None ):
        """
        create the environment to run a job
          - working directory creation
          - fixing permission
          - creation of the xml file index.xml
        """
        basedir =  self.cfg.results_path() 
        if not os.path.exists( basedir ):
            msg = "directory " + str( basedir ) + " does not exist"
            j_log.error(msg)
            raise MobyleError, msg
        if uri is None:            
            if self.session and self.service.getUrl().startswith(self.session.url):
                name = 'user_defined'
            else:
                name = self.service.getName()
            workdir = os.path.join( basedir , name , self.key )
            if os.path.exists( workdir ):
                msg = 'cannot make directory '+ str( workdir )+" : File exists"
                j_log.error( msg )
                raise MobyleError , msg
        try:
            os.makedirs( workdir , 0755 ) #create parent directory
        except Exception , err:
            j_log.critical( "unable to create job directory %s: %s " %( workdir , err ), exc_info = True )
            raise MobyleError , "Internal server Error"

        os.umask(0022)
        self.work_dir = workdir
        resource.setrlimit( resource.RLIMIT_CORE , (0 , 0) )
        maxFileSize = self.cfg.filelimit()
        resource.setrlimit( resource.RLIMIT_FSIZE , ( maxFileSize , maxFileSize ) )
        self.date = time.localtime()
        
        #be careful the order of setting informations in state is important
        self.jobState = JobState( uri=workdir, service=self.service )        

        serviceName = self.service.getName()
        jobID = self.getURL()
        
        self.jobState.setName( self.service.getUrl() )
        self.jobState.setHost( self.cfg.root_url() )
        self.jobState.setID( jobID )
        self.jobState.setDate( self.date )
        if self.userEmail is not None:
            self.jobState.setEmail( self.userEmail )
        sessionKey = None
        if self.session is not None:
            sessionKey = self.session.getKey()
            self.jobState.setSessionKey( sessionKey )
        if self.workflowID is not None:
            self.jobState.setWorkflowID( self.workflowID ) 
        self.jobState.commit()
        self.sm.create( self.work_dir , Status( code= 0 ) ) # building

        try:
            remote_host = os.environ['REMOTE_HOST']
        except KeyError :
            remote_host = "UNKNOWN"
        try:
            ip_addr = os.environ['REMOTE_ADDR']
        except KeyError :
            ip_addr = 'local'
        
        remote =  ip_addr+"\\"+remote_host 

        ## Attention I'm building the job instance
        ## during the MobyleJob instanciation
        ## thus the job is not already add to the session
        ## this is done explicitly in the CGI when a value is submitted

        Admin.create( self.work_dir , remote , serviceName , jobID , 
                      userEmail = self.userEmail , 
                      sessionID = sessionKey , 
                      workflowID = self.workflowID )
        
    def _newKey(self):
        """
        @return: a unique key which serve to indentify a job
        @rtype: string
        """

        #for PBS/SGE jobname, the first char of tmp dir must begin by a letter
        letter = ascii_uppercase[ random.randrange( 0 , 26 ) ]
        #max 15 chars for PBS jobname
        strTime = "%.9f" % time.time()
        strTime = strTime[-9:]
        strPid = "%05d" % os.getpid()
        strPid = strPid.replace( '.' , '' )[ -5 : ]
        return letter + strPid + strTime

    def setSession(self , session ):
        self.session = session
        sessionKey = self.session.getKey() 
        self.jobState.setSessionKey( sessionKey )
        self.jobState.commit()
        adm = Admin( self.work_dir )
        adm.setSession( sessionKey )
        adm.commit()
        
    def getKey( self ):
        """
        @return: the unique key of this job
        @rtype: string
        """
        return  self.key

    def getDate( self ):
        """
        @return: the submission date of this job
        @rtype: string
        """
        return  self.date
    

    def getDir(self):
        """
        @return: the absolute path to the directory where the job is executed
        @rtype: string
        """
        return self.work_dir

    def getURL(self):
        """
        @return: the URL to the directory where the job is executed
        @rtype: string
        """
        url = path2url( self.work_dir )
        return url

    def getService( self ):
        """
        @return: the instance of the service used for this job
        @rtype: Service
        """
        return self.service

    def getEmail( self ):
        """
        @return: the email of the user or None if there is no email
        @rtype: -L{Net.EmailAddress} instance
        """
        return self.userEmail

    def isLocal(self):
        """
        @return: True if this job is on this server , False otherwise
        @rtype: boolean
        """ 
        return self.jobState.isLocal()
        
    def run( self ):
        """
        Run the Job (instanciate a CommandRunner)
        @call: L{MobyleJob.run <MobyleJob>}
        """
        from Mobyle.RunnerFather import CommandRunner
        
        if self.jobState is None:
            msg = "you must make an environment for the job before running it"
            self._logError( logMsg = msg ,
                            userMsg = "Mobyle Internal server error"
                            )
            
            raise MobyleError, msg

        oldStatus = self.sm.getStatus( self.work_dir )
        if oldStatus != Status( string="building" ):
            msg = "try to run a Job which have %s status" % oldStatus
            self._logError( logMsg = msg ,
                            userMsg = "Mobyle Internal server error"
                            )
            
            raise MobyleError, msg
        self.sm.setStatus( self.work_dir , Status( code = 1 ) )#submitted

        self.runner = CommandRunner( self )
        cmdLine = self.runner.getCmdLine()
        debug = self.cfg.debug( self.service.getName() )

        if debug > 0 and debug < 3:# the job will not run
            self.sm.setStatus( self.work_dir , Status( code = 4 ) )#finished
        else:
            if self.userEmail is not None :
                self.over_limit( self.userEmail , cmdLine )
            self.runner.run()
        

    def kill( self ) :
        adm = Admin( self.getDir() )
        jobNum = adm.getNumber()
        if jobNum is None:
            raise MobyleError( "no jobNum for the job : %s" % self.ID )
        try:
            execKlass = executionLoader( jobID = self.ID )
            execKlass.kill( jobNum )            
            self.sm.setStatus( self.work_dir , Status( code= 6 , message = "Your job has been cancelled" ) )
        except MobyleError , err :
            msg = "cannot kill job %s : %s" % ( self.ID , err)
            j_log.error( msg ) 
            raise MobyleError( msg )
        
    def over_limit( self, userEmail , cmdLine ):
        """
        @param userEmail: the email address of the user
        @type userEmail: -L{Net.EmailAddress} instance
        @param cmdLine: the shell commandLine to execute
        @type cmdLine: string
        @raise UserValueError: if the number of similar jobs exceed the Config.SIMULTANEOUS_JOBS
        """
        newMd5 = md5()
        newMd5.update( str( userEmail ) )
        try:
            remote = os.environ[ 'REMOTE_HOST' ]
            if not remote :
                try:
                    remote = os.environ[ 'REMOTE_ADDR' ]
                except KeyError :
                    remote = 'no web'
        except KeyError:
            try:
                remote = os.environ[ 'REMOTE_ADDR' ]
            except KeyError:
                remote = 'no web'
                
        newMd5.update( remote )
        newMd5.update( cmdLine )
        newDigest = newMd5.hexdigest()
        
        thisJobAdm = Admin( self.work_dir )
        thisJobAdm.setMd5( newDigest )
        thisJobAdm.commit()

        mask = os.path.normpath( "%s/%s.*" %(
            self.cfg.admindir() ,
            self.service.getName()
            )
                                 )
        jobs = glob.glob( mask )
        max_jobs = self.cfg.simultaneous_jobs()
        
        if max_jobs == 0 :
            return 
        
        nb_of_jobs = 0
        msg = None
        for job in jobs:
            try:
                oldAdm = Admin( job )
            except MobyleError, err :
                if os.path.lexists( job ):
                        j_log.critical( "%s/%s: invalid job in ADMINDIR : %s" %( self.service.getName() ,  self.key , err ) )
                continue
            if( oldAdm.getWorkflowID() ):
                #we allow a workflow to run several identical job in parallel
                continue
            
            oldDigest = oldAdm.getMd5()
            if newDigest == oldDigest :
                oldStatus = self.sm.getStatus( self.work_dir ) 
                if not oldStatus.isEnded() :
                    nb_of_jobs += 1
                    if nb_of_jobs >= max_jobs:
                        msg = "%d similar jobs (%s) have been already submitted (md5 = %s)" % (
                                                                                      nb_of_jobs ,
                                                                                      os.path.basename( job ),
                                                                                      newDigest
                                                                                      )
                        userMsg = " %d similar job(s) have been already submitted, and are(is) not finished yet. Please wait for the end of these jobs before you resubmit." % ( nb_of_jobs )
                        self._logError( logMsg = msg + " : run aborted " ,
                                        userMsg = userMsg
                                        )
                        raise UserValueError( parameter = None, msg = userMsg )
                    
        return 



    def _logError( self , userMsg = None , logMsg = None ):

        if userMsg :
            self.sm.setStatus( self.work_dir , Status( code = 5 , message = userMsg ) ) #error

        if logMsg :
            j_log.error( "%s : %s : %s" %( self.service.getName() ,
                                          self.getKey() ,
                                          logMsg
                                          )
                        )
            
