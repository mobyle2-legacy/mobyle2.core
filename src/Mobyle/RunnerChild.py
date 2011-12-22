#! /usr/bin/env python


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
import sys
import glob
import time
import cPickle
import atexit

#"the environment variable MOBYLEHOME must be defined in the environment"
#append Mobyle Home to the search modules path
MOBYLEHOME = None
if os.environ.has_key('MOBYLEHOME'):
    MOBYLEHOME = os.environ['MOBYLEHOME']
if not MOBYLEHOME:
    sys.exit('MOBYLEHOME must be defined in your environment')

if ( os.path.join( MOBYLEHOME , 'Src' ) ) not in sys.path:
    sys.path.append(  os.path.join( MOBYLEHOME , 'Src' )  )


from Mobyle.MobyleLogger import MLogger
MLogger( child = True )

from logging import getLogger
rc_log = getLogger( 'Mobyle.RunnerChild' )

from Mobyle.JobState import JobState
from Mobyle.Utils import executionLoader , zipFiles , emailResults
from Mobyle.Net import EmailAddress
from Mobyle.Status import Status
from Mobyle.StatusManager import StatusManager
from Mobyle.Admin import Admin
from Mobyle.MobyleError import MobyleError
from Mobyle.ConfigManager import Config
from Mobyle.Registry import registry
_cfg = Config()

__extra_epydoc_fields__ = [('call', 'Called by','Called by')]


class AsynchronJob:
    """
    is instantiated in child process instantiate the object corresponding
    to the execution manager defined in Config, and after the completion of the job
    manage the results
    """

    
    def __init__(self, commandLine, dirPath, serviceName, resultsMask , userEmail = None, email_notify = 'auto' , jobState = None , xmlEnv = None):
        """
        @param commandLine: the command to be executed
        @type commandLine: String
        @param dirPath: the absolute path to directory where the job will be executed (normaly we are already in)
        @type dirPath: String
        @param serviceName: the name of the service
        @type serviceName: string
        @param resultsMask: the unix mask to retrieve the results of this job
        @type resultsMask: a dictionary { paramName : [ string prompt , ( string class , string or None superclass ) , string mask ] }
        @param userEmail: the user email adress
        @type userEmail: string
        @param email_notify: if the user must be or not notify of the results at the end of the Job.
        the 3 authorized values for this argument are: 
          - 'true' to notify the results to the user
          - 'false' to Not notify the results to the user
          - 'auto' to notify the results based on the job elapsed time and the config  EMAIL_DELAY
        @type email_notify: string 
        @param jobState: the jobState link to this job
        @type jobState: a L{JobState} instance
        @param xmlEnv: the environement variable need by the program
        @type xmlEnv: dictionnary
        @call: by the main of this module which is call by L{AsynchronRunner}
        """
        self._command = commandLine
        self._dirPath = dirPath
        self.serviceName = serviceName
        self.father_pid = os.getppid()
        self.father_done = False
        if jobState is None:
            self.jobState = JobState( self._dirPath )
        else:
            self.jobState = jobState
        self.userEmail = userEmail
        self.email_notify =  email_notify 
        
        if self._dirPath[-1] == '/':
            self._dirPath = self._dirPath[:-1]

        self.jobKey = os.path.split( self._dirPath )[ 1 ]
        
        atexit.register( self.childExit , "------------------- %s : %s -------------------" %( serviceName , self.jobKey ) )
        
        t0 = time.time()
        ############################################
        self._run( serviceName , xmlEnv )
        #############################################
        t1 = time.time()
        
        self.results = {}
        for paramName in resultsMask.keys():
            resultsFiles = []
            #type is a tuple ( klass , superKlass )
            masks = resultsMask[ paramName ]
            for mask in masks :
                for File in  glob.glob( mask ):
                    size = os.path.getsize( File )
                    if size != 0:
                        resultsFiles.append(  ( str( File ) , size , None ) ) #we have not information about the output format 
            if resultsFiles: 
                self.results[ paramName ] = resultsFiles  #a list of tuple (string file name , int size ,  string format or None )
                self.jobState.setOutputDataFile( paramName , resultsFiles )

        self.jobState.commit()
        try:
            zipFileName = self.zipResults()
        except Exception :
            msg = "an error occured during the zipping results :\n\n"
            rc_log.critical( "%s/%s : %s" %( self.serviceName , self.jobKey , msg ) , exc_info = True)
            zipFileName = None
        if self.userEmail:
            if self.email_notify == 'auto':
                # we test email_delay() to see if it is >= to 0, 
                # as it seems that sometimes it is not >0.
                if ( t1 - t0 ) >= _cfg.email_delay():
                    emailResults(_cfg,
                                       self.userEmail,
                                       registry ,
                                       self.jobState.getID(),
                                       self._dirPath ,
                                       self.serviceName ,
                                       self.jobKey ,
                                      FileName = zipFileName )
            elif self.email_notify == 'true':
                emailResults( _cfg,
                                   self.userEmail,
                                   registry ,
                                   self.jobState.getID(),
                                   self._dirPath ,
                                   self.serviceName ,
                                   self.jobKey ,  
                                   FileName = zipFileName )
            else:
                pass    

    def childExit(self , message ):
        print >> sys.stderr , message
        #rc_log.log( 12 , "runnerChild %d ending, send a SIGCHLD to %d" %( os.getpid() , self.father_pid ) )

    def _run(self , serviceName, xmlEnv ):
        dispatcher = _cfg.getDispatcher()
        
        execution_config = dispatcher.getExecutionConfig( self.jobState )
        try:
            exec_engine = executionLoader( execution_config =  execution_config )
        except MobyleError ,err :
            msg = "unknown execution system : %s" %err
            rc_log.critical("%s : %s" %( serviceName ,
                                         msg
                                         ), exc_info = True 
            )
            sm = StatusManager()
            sm.setStatus( self._dirPath , Status( code = 5 , message = 'Mobyle internal server error' ) )
            raise MobyleError, msg
        except Exception , err:
            rc_log.error( str(err ), exc_info=True) 
            raise err
        
        exec_engine.run( self._command , self._dirPath , serviceName ,  self.jobState , xmlEnv )
        
    
    def zipResults(self ):    
        files2zip = []

        for Files in self.results.values():
            for File in Files:
                files2zip.append( ( File[0] , os.path.basename( File[0]) ) ) #File is tuple (string file name , int size , string format or None )
        
        xsl_path = os.path.join( _cfg.portal_path() , "xsl" ,)
        jobXslPath = os.path.join( xsl_path , "job.xsl" ) 
        files2zip.append( ( jobXslPath , "job.xsl" ) )
                
        identXslPath = os.path.join( xsl_path , "ident.xsl" )
        files2zip.append( ( identXslPath , "ident.xsl" ) )

        cssPath = os.path.join( _cfg.portal_path() , "css",  "mobyle.css" ) 
        files2zip.append( ( cssPath , "mobyle.css" ) )

        
        paramsfiles = self.jobState.getParamfiles()
        if paramsfiles: 
            for paramsfile in paramsfiles:
                files2zip.append( ( os.path.join( self._dirPath , paramsfile[0] ) , paramsfile[0] ) )
        
        inputFiles = self.jobState.getInputFiles() #inputFiles = [ ( parameterName , [ (fileName , format or None ) , ...) , ... ]
        if inputFiles is not None:
            for files in inputFiles:
                for item in files[1]: #item = ( filename , size , fmt ) 
                    files2zip.append( ( os.path.join( self._dirPath , item[0] ) , item[0] ) )
        
        files2zip.append( ( os.path.join( self._dirPath , "index.xml") , "index.xml" ) )
        zipFileName = "%s_%s.zip" %(self.serviceName , self.jobKey )    
        zip_filename = zipFiles( zipFileName , files2zip )
        return  zip_filename    

if __name__ == '__main__':
    try:
        fh = open(".forChild.dump", "r")
        fromFather = cPickle.load( fh )
        fh.close() 
    except Exception, err :
        rc_log.critical( str( err ) )
        raise MobyleError( err )

    try:
        os.chdir( fromFather[ 'dirPath' ] )
    except OSError, err:
        msg = fromFather[ 'serviceName' ] + ":" + str( err )
        rc_log.critical( msg )
        raise MobyleError ,msg

    userEmail = fromFather[ 'email']
    if userEmail is not None:
        userEmail = EmailAddress( userEmail  )
        
    child = AsynchronJob( fromFather[ 'commandLine' ] , # string the unix command line
                          fromFather[ 'dirPath' ] ,     # absolute path of the working directory
                          fromFather[ 'serviceName' ] , # string 
                          fromFather[ 'resultsMask'] ,  # 
                          userEmail = userEmail  ,      # Net.EmailAddress to
                          xmlEnv = fromFather[ 'xmlEnv' ] , #a dict
                          email_notify = fromFather[ 'email_notify' ] #'true' , 'false' or 'auto'
                          )
