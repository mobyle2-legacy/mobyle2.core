########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.        #
#                                                                                      #
########################################################################################


import os
import logging 
import types
import glob

from Mobyle.MobyleLogger import MLogger
MLogger()

from Mobyle.Net import EmailAddress , checkHost
from Mobyle.MobyleError import MobyleError , UserValueError , UnDefAttrError , ServiceError ,UnSupportedFormatError , EvaluationError
from Mobyle.Job import Job
from Mobyle.Evaluation import Evaluation
from Mobyle.JobState import JobState , url2path as jobState_url2path
from Mobyle.Utils import getStatus as utils_getStatus , safeFileName , makeService
from Mobyle.Status import Status
from Mobyle.StatusManager import StatusManager
from Mobyle.Admin import Admin

_extra_epydoc_fields__ = [('call', 'Called by','Called by')]

     

class MobyleJob:
    """this class is the interface with the cgis to submit a job"""
    
    def __init__(self, progUrl= None , email = None , service = None, params = None, evaluator = None , ID = None , session = None , cfg = None , workflowID = None , email_notify= 'auto'):
        """
        We could instanciate a MobyleJob whith a progName or directly with a Service instance , with params or a Evaluation instance.
        if we instanciate a MobyleJob with a progName mobyleJob will instanciate a service corresponding to this name .
        you could provide the user parameters in a dictionary params which will used to fill an Evalution instance or provide directly the Evaluation instance.
        
        @param progUrl: the url of a xml file
        @type progUrl: String
        @param email: the user Email address where the results will be sent
        @type email: string or L{EmailAddress}
        @param service: if you want to run a service which is already instanciate
        @type service: a L{Service} instance
        @param evaluator: an Evaluation instance
        @type evaluator: L{Evaluation} 
        @param ID: the url of job, if an id is specified 
        @type ID: string
        @param cfg: a config object
        @type cfg: L{ConfigManager.Config} instance
        @param workflowID: the url of the workflow ownre of this job
        @type workflowID: string
        @param email_notify: if the user must be or not notify of the results at the end of the Job.
        the 3 authorized values for this argument are: 
          - 'true' to notify the results to the user
          - 'false' to Not notify the results to the user
          - 'auto' to notify the results based on the job elapsed time and the config  EMAIL_DELAY
        @type email_notify: string 
        @raise L{MobyleError}: if the id is not a valid url a MobyleError is raised
        @todo: estce que passer un evaluateur a MobyleJob a toujours un sens avec la nouvelle architecture (creation de fichiers ... l'evaluateur a un nom de fichier comme valeur comment recuperer le contenu)
        """
        self.m_log = logging.getLogger( __name__ )
        if cfg is None:
            from Mobyle.ConfigManager import Config
            self.cfg = Config()
        else:
            self.cfg = cfg
            
        if ID:
            self.jobState = JobState( ID )
            self._job = None
            self._hasRun = True
        else:
            self.build_log = logging.getLogger('Mobyle.builder')
            
            if progUrl:
                jobName = os.path.basename( progUrl )[:-4]
            elif service:
                jobName = service.getName()
            else:
                raise MobyleError, "you must provide either a service or a service name"

            ## check the service availablity
            serviceID = 'local.'+jobName
            if self.cfg.isDisabled( serviceID  ):
                if self.cfg.isDisabled():
                    raise MobyleError, "Sorry, the server is not available for now."
                else:
                    raise MobyleError, "Sorry, the program " + jobName +" is  not available for now."
            try:
                remoteHost = os.environ[ 'REMOTE_HOST' ]
            except KeyError:
                remoteHost = None
            try:
                ip = os.environ[ 'REMOTE_ADDR' ]
            except KeyError :
                ip = 'local'
            self._remote =( ip , remoteHost )
            if  self._remote[1]:
                remoteLog = self._remote[1]  #the remote host    
            else:
                remoteLog  = self._remote[0] #the remote addr
            if session :
                email = session.getEmail()
                if email:
                    self.userEmail = EmailAddress( session.getEmail() )
                else:
                    self.userEmail = None
            elif email :
                if  isinstance( email , types.StringTypes ):
                    self.userEmail = EmailAddress( email )
                else:
                    self.userEmail = email
                chk = self.userEmail.check()
                if not chk:
                    msg = self.userEmail.getMessage()
                    userMsg = "you are not allowed to run on this server for now "
                    
                    msg = "%s %s %s %s" %( jobName ,
                                           unicode( str( self.userEmail ).decode('ascii', 'replace')).encode( 'ascii', 'replace' ) ,
                                           remoteLog ,
                                           "FORBIDDEN "+ msg
                                           )
                    self.m_log.info( msg )
                    raise UserValueError( msg = userMsg )                 
            else:
                self.userEmail = None
            email_notify = email_notify.lower()
            try:
                checkHost()
            except UserValueError ,err:
                msg = "%s %s %s %s %s" %( jobName,
                                          unicode( str( email ).decode('ascii', 'replace')).encode( 'ascii', 'replace' ) ,
                                          remoteLog ,
                                          "FORBIDDEN ",
                                           err
                                          )
                
                self.m_log.info( msg )
                raise UserValueError( msg = "you are not allowed to run a job on this server for now " )

            ## building the MobyleJob
            self.progUrl = progUrl
            self._service = service
            self.params = params # a garder??
            self._evaluator = evaluator
            self.session = session
            self._job = None             #an instance of Mobyle.Job
            self.jobState = None       #an instance of JobState
            self._adm = None
            self._hasRun = False
            
            if params is None:
                if service is None:
                    if progUrl is None:
                        ### TODO il n'y a pas encore de job de cree donc logger cette erreur ?
                        raise MobyleError, "you must provide either a service or a service url"
                    else:
                        if evaluator is None or not evaluator.isFill():
                            #self._service = self._makeService( progUrl )
                            try:
                                self._service = makeService( progUrl )
                            except MobyleError , err :
                                
                                self._logError( userMsg = "Mobyle internal server error" )
                                raise MobyleError( err )
                            self._service = makeService( progUrl )
                            self._evaluator = self._service.getEvaluator()
                        else:
                            if evaluator.isFill():
                                try:
                                    self._service = makeService( progUrl )
                                except MobyleError , err :
                                    self._logError( userMsg = "Mobyle internal server error")
                                    raise MobyleError( err )

                                self._service.setEvaluator( evaluator )
                else: #service is not None
                    if self._evaluator is None or not self._evaluator.isFill():
                        self._evaluator = self._service.getEvaluator()
                    else:
                        self._service.setEvaluator( evaluator )
                self._debug = self.cfg.debug( self._service.getName() )
                self._job = Job( self._service ,
                                            self.cfg ,
                                            userEmail = self.userEmail ,
                                            session = self.session ,
                                            workflowID = workflowID ,
                                            email_notify = email_notify
                                            )
            else: #params is not None
                if service is None:
                    if progUrl is None:
                        raise MobyleError,"you must provide either a service a service url"
                    else:
                        self._service = makeService( progUrl )
                        self._evaluator = self._service.getEvaluator()
                else: #service is not None
                    self._evaluator = Evaluation()
                    self._service.setEvaluator( self._evaluator )
                self._debug = self.cfg.debug( self._service.getName() )
                self._job = Job( self._service ,
                                            userEmail = self.userEmail ,
                                            session = self.session ,
                                            workflowID = workflowID ,
                                            email_notify = email_notify
                                            )
                
            ############ in all cases except ID ###################

            if self._debug > 1:
                self.build_log.debug( "MobyleJob : params= " + str( params ) )
            self.jobState = self._job.jobState
            self._adm = Admin( self._job.getDir() )


    ###############################################################
    #
    #                
    #
    ###############################################################

    def setSession(self , session ):
        self.session = session
        if self._job is not None:
            self._job.setSession( session )
        
    def setValue( self , paramName , value ):
        """
        set the value for one parameter. the value is cast in the right type. if the value cannot be cast a UserValueError is raised
        @param paramName: the name of the parameter
        @type paramName: string
        @param value : the value of the parameter
        @type value:
           - for simple type: any
           - for the infile: a tuple ( destFileName , content , src , srcFileName )
             - the name of the file
             - the data the content of the file , string or None 
             - the src where the file could be retrieve, MobyleJob , Job or Session instance or None
        data is specified when data is new on the server.
        src is specified when the data already exists on the server.
        you can't specify data and src in the same time
        @raise: MobyleError if the paramName doesn't match with any parameter name
        """
        if self._hasRun:
            msg = "MobyleJob.setValue this job has already ran"
            self._logError( logMsg = msg ,
                            userMsg = msg
                            )
            raise MobyleError , msg
        
        if self._debug > 1:
            self.build_log.debug( "\n--------------------- MobyleJob set user value for " + paramName + "--------------------" )        
        if paramName in  self._service.getAllParameterNameByArgpos():
            parameter = self._service.getParameter( paramName )
            acceptedMobyleType = parameter.getType()
            dataType = acceptedMobyleType.getDataType()
            if value == '' :
                value = None
            if self._service.isInfile( paramName ):
                if len( value ) == 4 : ###MobyleJob is called from a cgi
                    destFileName , data  , src , srcFileName = value
                    if not destFileName and not data and not src:
                        data  = None
                        src = None
                    elif destFileName and not ( data or src ):
                        msg = "parameter %s: is empty. please check your data" % paramName
                        self._logError( logMsg = msg ,
                                        userMsg = msg
                                        )
                        raise UserValueError( parameter =  parameter , msg = msg )
                    elif data and src:
                        msg = "parameter %s: you cannot specify data and source at the same time" % paramName
                        self._logError( logMsg = msg ,
                                        userMsg = msg
                                        )
                        raise UserValueError( parameter =  parameter , msg = msg )

                    elif not srcFileName and not data and src:
                        msg = "parameter %s: if you specify a src, you must specify a src file name" % paramName
                        self._logError( logMsg = msg ,
                                        userMsg = msg
                                        )
                        raise UserValueError( parameter =  parameter , msg = msg )
                       
                    elif not srcFileName and data and not src:
                        srcFileName = paramName + ".data"      

                                        
                    # I put systematically the value in index.xml even if its the
                    # same as the previous value because the value is a filename 
                    # and 2 files with the same name could have different contents
                    
                    ##fileName = basename
                    try:
                        fileName, sizeIn = dataType.toFile( data, self._job , destFileName, src , srcFileName )
                    except MobyleError, err:
                        msg = "%s/%s : %s : %s"%( self._service.getName(), self.getJobid() , paramName, err)
                        self.m_log.error( msg )
                        raise MobyleError( msg )
                    detectedMobyleType = acceptedMobyleType.detect( ( self._job, fileName ) )
                    acceptedFormats = acceptedMobyleType.getAcceptedFormats()
                    if detectedMobyleType.dataFormat is None :
                        self.jobState.setInputDataFile( paramName ,
                                                        ( fileName  ,  sizeIn ,  'not detected' ) ,
                                                        )
                        self.jobState.commit()
                        
                        if not acceptedFormats:
                            parameter.setValue( fileName )    
                        elif ( set( [ f for f , r in acceptedFormats] )- set( dataType.supportedFormat() ) ):
                            # format accepted by the parameter  -  format supported by the conevrters
                            # case of a not detected format but the parameter accept some formats not supported by converter
                            self.m_log.warning("%s/%s : %s : a data format which has not been detected has been accepted in job" %( self._service.getName(), self.getJobid() , paramName ))
                            parameter.setValue( fileName )
                        else:
                            # case of a not detected format and the all format accepetd by the parameter are supported by the converters 
                            msg = "Your %s format cannot be detected: please submit your data in one of the following formats: %s"%( dataType.getName() , dataType.supportedFormat() )
                            sm = StatusManager()
                            sm.setStatus( self.getDir() , Status( code= 5 , message= msg ))
                            raise UserValueError( parameter = parameter ,
                                                  msg = msg )
                    else: #the format of the data has been detected
                        outFileName = None
                        if not acceptedFormats:#if there isn't any accepted format => all formats are available
                            self.jobState.setInputDataFile( paramName ,
                                                                    ( fileName  ,  sizeIn ,  detectedMobyleType.dataFormat ) ,
                                                                    fmtProgram = detectedMobyleType.format_program
                                                                    )
                            self.jobState.commit()
                            parameter.setValue( fileName )
                            if self._debug > 1:
                                    self.build_log.debug("self._service.setValue( %s , %s )" %( paramName , fileName ) )
                        else:# some accepted format are specified
                            for out_format , force_reformat in acceptedFormats:
                                if detectedMobyleType.dataFormat == out_format:
                                    if force_reformat:
                                        continue
                                    else:
                                        self.jobState.setInputDataFile( paramName ,
                                                                        ( fileName  ,  sizeIn ,  detectedMobyleType.dataFormat ) ,
                                                                        fmtProgram = detectedMobyleType.format_program
                                                                        )
                                        self.jobState.commit()
                                        outFileName = fileName
                                        break
                                else:
                                    continue
                            
                            if outFileName is None:#the data must be converted
                                try:
                                    outFileName , convertedMobyleType = detectedMobyleType.convert( ( self._job, fileName ) , acceptedMobyleType )
                                    
                                    sizeOut = os.path.getsize( os.path.join( self._job.getDir(),outFileName ) )
                                    self.jobState.setInputDataFile( paramName ,
                                                                    ( fileName  ,  sizeIn ,  detectedMobyleType.dataFormat ) ,
                                                                    fmtProgram = convertedMobyleType.format_program ,
                                                                    formattedFile = ( outFileName , sizeOut , convertedMobyleType.dataFormat )
                                                                    )
                                    self.jobState.commit()
                                except UnSupportedFormatError ,err :
                                    msg = str( err )
                                    sm = StatusManager()
                                    sm.setStatus( self.getDir() , Status( code= 5 , message= msg ))
                                    raise UserValueError( parameter = parameter , msg = msg )
                            parameter.setValue( outFileName )
                            if self._debug > 1:
                                    self.build_log.debug("self._service.setValue( %s , %s )" %( paramName , outFileName ) )

                else:
                        msg = "Problem with the infile : " + paramName
                        self._logError( logMsg = msg ,
                                        userMsg = "Internal Mobyle Server Error"
                                        )
                        raise UserValueError( parameter = parameter , msg = msg )
                    
            else : #the parameter is not an infile
                oldValue = parameter.getValue()
                try:
                    detectedMobyleType = dataType.detect( value )
                    converted_value , convertedMobyleType = detectedMobyleType.convert( value , acceptedMobyleType )
                    parameter.setValue( converted_value )
                    if self._debug > 1:
                        try:
                            self.build_log.debug( "self._service.setValue( %s , %s )" %( paramName , converted_value ) )
                        except:
                            self.build_log.debug( "!!!!!!!! problem during reporting log !!!!!!!!!!!!" )
                except UserValueError , err:
                        msg =  str( err )
                        self._logError( logMsg = msg ,
                                        userMsg = msg
                                        )
                        raise UserValueError(parameter=parameter, msg=msg)
                    
                newValue = parameter.getValue( )
                if newValue != oldValue :
                    rawVdef =  parameter.getVdef()
                    if rawVdef is None:
                        vdef = None
                    else:
                        vdef , vdefMT = detectedMobyleType.convert( rawVdef , acceptedMobyleType )
                        if parameter.getType().getDataType().getName() == 'MultipleChoice':
                            sep = parameter.getSeparator()
                            vdef = sep.join( vdef)
                    if newValue == vdef :
                        if oldValue is not None and oldValue != vdef:
                            self.jobState.delInputData( paramName )
                            self.jobState.commit()
                    else:
                        self.jobState.setInputDataValue( paramName , newValue )
                        self.jobState.commit()
        else:
            msg = "the parameter named : %s doesn't exist in %s" %( paramName ,
                                                                    self._service.getName()
                                                                    )
            self._logError( logMsg = msg ,
                            userMsg = msg
                            )
            raise UserValueError( msg = msg )



    def _validateParameters(self):
        """
        verifie que le parametre est valide cad si c'est un choice qu'il appartient bien a la liste si c'est une sequence passe dans squizz ...
        @raise UserValueError: throws UserValueError raised by checkUser
        """
        if self._debug > 1:
            self.build_log.debug("""\n
              \t################################################
              \t#                                              #
              \t#              validation beginning            #
              \t#                                              #
              \t################################################
              \n""")
                
        for paramName in self._service.getAllParameterNameByArgpos():
            ###################################################
            #                                                 #
            #         check if parameter have a value         #
            #                                                 #
            ###################################################
            
            value = self._service.getValue(paramName)
            if self._debug > 1:
                self.build_log.debug("------------- " + paramName + " -------------")
                self.build_log.debug("value= %s : type= %s"%( value , type(value) ) )
                self.build_log.debug("service.precondHas_proglang( %s , 'python' ) = %s " %(
                    paramName ,
                    self._service.precondHas_proglang( paramName , 'python' )
                    )
                            )
                    
            if self._service.precondHas_proglang( paramName , 'python' ):
                preconds = self._service.getPreconds( paramName , proglang='python' )
                allPrecondTrue = True
                for precond in preconds:
                    try:
                        evaluatedPrecond = self._evaluator.eval( precond )
                    except EvaluationError, err:
                        self.build_log.error("ERROR during precond evaluation: %s : %s"%( precond, err ) )
                        msg = "ERROR during %s %s precond evaluation: %s : %s" % ( self._service.getName(),
                                                                                  paramName ,
                                                                                  precond ,
                                                                                  err
                                                                                 )
                        self._logError( logMsg = msg ,
                                        userMsg = "Internal Server Error"
                                        )
                        raise MobyleError( "Internal Server Error" )
                    
                    if self._debug > 1:
                        self.build_log.debug("precond= " + precond )
                        self.build_log.debug("eval precond= " + str( evaluatedPrecond ))
                        
                    if not evaluatedPrecond :
                        allPrecondTrue = False
                        break
                
                if not allPrecondTrue :
                    if self._debug > 1:
                        self.build_log.debug("next parameter")
                    continue #next parameter
            else:
                if self._debug > 1:
                    if self._service.precondHas_proglang( paramName, 'perl' ) :
                        self.build_log.debug( "################ WARNING ###################" )
                        self.build_log.debug( "had a precond code in Perl but not in Python" )
                        self.build_log.debug( "############################################" )
            if value is None :
                if self._debug > 1:
                    self.build_log.debug( " value is None " )
                if self._service.ismandatory( paramName ):
                    msg = "The mandatory Parameter : %s, must be specified " % paramName
                    self._logError( logMsg = msg ,
                                    userMsg = msg
                                    )

                    raise  UserValueError(parameter = self._service.getParameter( paramName ) ,
                                          msg = "This parameter is mandatory" )
            
            if self._debug > 1:
                self.build_log.debug( "call service.validate( " + paramName + " )" )
            try:    
                self._service.validate( paramName )
            except UserValueError , err:
                msg = str(err)
                self.build_log.debug( msg )
                self._logError( logMsg = msg ,
                                userMsg = msg
                                )
                raise UserValueError ,err
            
            except MobyleError , err:
                msg = str(err)
                self.build_log.debug( msg )
                self._logError( logMsg = msg ,
                                userMsg = "Mobyle Internal Server Error"
                                )                
                raise MobyleError , err
            ####################################################
            #                                                  #
            #  check if the Parameter have a secure paramfile  #
            #                                                  #
            ####################################################

            try:
                if self._debug > 1:
                    self.build_log.debug( "check if the Parameter have a secure paramfile" )

                paramfile = self._service.getParamfile( paramName )
                try:
                    safeParamfile = safeFileName( paramfile )
                except UserValueError , err :
                    msg = str( err )
                    self._logError( logMsg = msg ,
                                    userMsg = msg
                                    )
                    raise UserValueError( parameter= self._service.getParameter( paramName ), msg = msg )
                
                if not safeParamfile or safeParamfile != paramfile :
                    msg = "The Parameter:%s, have an unsecure paramfile value: %s " %(  paramName ,
                                                                                        paramfile
                                                                                        )
                    if self._debug < 2 :
                        self._logError( logMsg = None ,
                                        userMsg = "Mobyle Internal Server Error"
                                        )
                        
                        self.m_log.critical( "%s/%s : %s" %( self._service.getName(),
                                                          self._job.getKey() ,
                                                          msg
                                                          )
                                        )
                    else:
                        self._logError( logMsg =  msg ,
                                        userMsg = "Mobyle Internal Server Error"
                                        )


                    raise MobyleError , "Mobyle Internal Server Error"
                else:
                    if self._debug > 1:
                        self.build_log.debug( "paramfile = %s ...........OK" % paramfile )
            except UnDefAttrError :
                if self._debug > 1:
                    self.build_log.debug("no paramfile")
                pass
        
        
    def _collisions(self):
        """
        check if there is no potential collisions between the infiles and the output masks.
        if ther is a risk of collision the input file is renamed
        """
        paramsOut = self._service.getAllOutParameter(  )
        evaluator = self._service.getEvaluator()
        allMasks = []
        potCollisions =[]
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
            unixMasks = self._service.getFilenames( paramName , proglang = 'python' )
            service_name = self._service.getName()
            unixMasks += ["%s.out"%service_name , "%s.err"%service_name ]
            allMasks += unixMasks 
            workdir = self.getDir()
            for mask in unixMasks:
                mask = os.path.join( workdir , mask )
                Files = glob.glob( mask )
                if Files:
                    self.m_log.warning( 'Potential Collision: %s input files match the \"%s\" output parameter mask %s' %( Files ,
                                                                                                                           paramName,
                                                                                                                           mask
                                                                                                                           ) )
                    potCollisions += [ os.path.basename( f ) for f in  Files ]

        infiles = self._service.getAllInFileParameter()            
        for infileName in potCollisions:
            for parameter in infiles:
                oldName = parameter.getValue()
                if oldName == infileName:
                    newName = "mob_%s_collision" %( infileName )
                    parameter.renameFile(  workdir , newName  )
                    self.jobState.renameInputDataFile( parameter.getName() , newName )
                    self.jobState.commit()
                    self.m_log.warning( '%s/%s : Potential Collision : %s file was renamed into %s' %( self._service.getName(),
                                                                                                      self._job.getKey() ,
                                                                                                      oldName ,
                                                                                                      newName )
                    )
        
        for mask in allMasks :
            mask = os.path.join( workdir , mask )
            collideFiles = glob.glob( mask )
            if collideFiles:
                msg= '%s/%s : Potential Collision: %s input files output mask %s' %( self._service.getName(),
                                                                                     self._job.getKey() ,
                                                                                     collideFiles ,
                                                                                     mask
                                                                                   ) 
                self._logError( userMsg = "Mobyle Internal Server Error", 
                                logMsg  = msg
                                )
                raise MobyleError , msg


    def run(self):
        """
        run a job
        @raise MobyleError: L{MobyleError} if the job dosen't exist. or if session is not activated
        """
        if self._job is not None:
            
            if not self.cfg.isAuthorized( self._service.getName() , self._remote[0] ):
                msg = "Sorry, you are not allowed to run this service."
                logMsg = " %s try to access restricted service"%self._remote[0]
                self._logError( userMsg = msg , 
                                logMsg = logMsg,
                                )                
                raise MobyleError( msg )
            
            if self.session and not self.session.isActivated():
                self._logError( userMsg = "session is not activated : run aborted" , 
                                logMsg = "session \"%s\" is not activated : run aborted" % self.session.getKey() 
                                )
                raise MobyleError( "session is not activated" )
            
            # for security reason 
            # I remove some unsuful variable form environment
            # to avoid to propagate them in all cluster nodes
            # waiting a better model 
            
            for envVar in [ 'CONTENT_LENGTH'      ,
                            'CONTENT_TYPE'        ,
                            'GATEWAY_INTERFACE'   ,
                            'HTTP_ACCEPT'         ,
                            'HTTP_ACCEPT_ENCODING',
                            'HTTP_ACCEPT_LANGUAGE',
                            'HTTP_CACHE_CONTROL'  ,
                            'HTTP_ACCEPT_CHARSET' ,
                            'HTTP_COOKIE'         ,
                            'HTTP_CONNECTION'     ,
                            'HTTP_KEEP_ALIVE'     ,
                            'HTTP_PRAGMA'         ,
                            'HTTP_REFERER'        ,
                            'HTTP_USER_AGENT'     ,
                            'HTTP_X_PROTOTYPE_VERSION',
                            'HTTP_X_REQUESTED_WITH',
                            'QUERY_STRING'        ,
                            'SERVER_ADMIN'        ,
                            'REQUEST_METHOD'      ,   
                            'REQUEST_URI'         ,
                            'SCRIPT_FILENAME'     ,
                            'SCRIPT_NAME'         ,
                            #'SERVER_NAME'         ,
                            #'SERVER_PORT'         ,
                            'SERVER_PROTOCOL'     ,
                            'SERVER_SIGNATURE'    ,
                            'SERVER_SOFTWARE'     ,

]:
                try:
                    del( os.environ[ envVar ])
                except KeyError:
                    pass
                    
            self._validateParameters()
                    
            #do the controls specified in the Xml file
            if self._debug > 1:
                self.build_log.debug("""\n
                \t################################################
                \t#                                              #
                \t#           xml controls beginning             #
                \t#                                              #
                \t################################################
                \n""")
            
            for paramName in self._service.getAllParameterNameByArgpos():
             
                hasCtrl = self._service.has_ctrl( paramName )
                hasScale = self._service.hasScale( paramName , proglang = 'python' )
             
                if hasCtrl or hasScale:

                    if self._debug > 1:
                        self.build_log.debug("------------- " + paramName + " -------------")
                        self.build_log.debug("service.precondHas_proglang( %s , 'python' ) = %s " %(
                            paramName ,
                            self._service.precondHas_proglang( paramName , 'python' )
                            ))
                        
                    if self._service.precondHas_proglang( paramName , 'python' ):
                        preconds = self._service.getPreconds( paramName , proglang='python' )
                        allPrecondTrue = True
                       
                        for precond in preconds:
                            evaluatedPrecond = self._evaluator.eval( precond )
                            
                            if self._debug > 1:
                                self.build_log.debug("precond= " + precond )
                                self.build_log.debug("eval precond= " + str( evaluatedPrecond ))
                            if not evaluatedPrecond :
                                allPrecondTrue = False
                                break
                        if not allPrecondTrue :
                            if self._debug > 1:
                                self.build_log.debug("next parameter")
                            continue #next parameter
                    if hasCtrl:
                        if self._service.getValue( paramName ) is not None:
                            try:
                                self._service.doCtrls( paramName )
                            except ServiceError , err:
                                # when the parameterName doesn't exist 
                                # or an error occured during the python code evaluation ( see parameter.doCrtls() )
                                msg = str( err )
                                self._logError( logMsg = msg , userMsg = "Internal Mobyle server Error" )
                                raise MobyleError , msg 
                            except UserValueError , err:
                                msg = str( err )
                                self._logError( logMsg = msg , userMsg = msg )
                                raise err
                        else:
                            if self._debug > 1:
                                self.build_log.debug("undefined value: next parameter")
                            continue
                    if hasScale:
                        if self._debug > 1:
                            self.build_log.debug( paramName + " has scale= True" )
                        try:
                            isInScale = self._service.isInScale( paramName , proglang = 'python')
                            if self._debug > 1:
                                self.build_log.debug( "isInScale= " + str( isInScale ) )
                            if isInScale:
                                continue
                            else:
                                smin ,smax , incr = self._service.getScale( paramName , proglang = 'python') 
                                msg = "%s value: %s is not in scale ( %s , %s )" %(
                                    paramName ,
                                    self._service.getValue( paramName ) ,
                                    smin ,
                                    smax )

                                self._logError( logMsg = msg , userMsg = msg )
                                parameter = self._service.getParameter( paramName )
                                raise UserValueError( parameter = parameter , msg = msg )
                            
                        except ValueError , err :
                            msg = paramName + " value is None. Thus it is not in scale"
                            self._logError(logMsg = msg , userMsg = msg )
                            raise MobyleError , msg
                    else:
                        if self._debug > 1:
                            self.build_log.debug("has scale= False" )

                            continue
            self._collisions()
                                             
            self._hasRun = True
            self._job.run()  
            return self._job.getURL()
        
        else:
            if self._hasRun:
                msg = "MobyleJob.run this job has already ran"
            else:
                msg = "MobyleJob.run: can't run the job (%s). It doesn't exist" % self._job.getURL() 

            self._logError( logMsg = msg , userMsg = msg )

            raise MobyleError , msg 
        


      
    
    ####################################################################
    #
    #                    get job info
    #
    ####################################################################

    def getDir(self):
        """
        @return: the directory absolute path where the job is executed
        @rtype: string
        @call: cgiJob.printResult()
        """
        if self._job:
            return self._job.getDir()
        elif self.jobState:
            url = self.jobState.getID()
            return jobState_url2path( url )
        else:
            return None

    def getDate(self):
        """
        @return: the submission date of this job
        @rtype: string
        @call: cgiJob.submit()
        """
        if self._job:
            return self._job.getDate()
        else:
            return None     

    def getJobid(self):
        """
        @return: url where the job is executed
        @rtype: string
        """
        if self.jobState:
            return self.jobState.getID()
        else:
            return None
        
    def getOutputs(self):
        """
        @return: a dictionary where the keys are the parameter name and the values a list of files which are produced by this parameter.
        @rtype: dict

        """
        if self.jobState:
            if self._hasRun:
                return self.jobState.getOutputs()
            else:
                msg = "try to get results but the job had not run"
                raise MobyleError , msg
        else:
            return None

    def getOutput(self , paramName ):
        """
        @return: the list of results files names. if there is no files for this parameter return None 
        @rtype: list of tuples ( string filename , long size , string fmt or None )
        """
        if self.jobState:
            if self._hasRun:
                return self.jobState.getOutput( paramName )
            else:
                msg = "try to get result but the job had not run"
                raise MobyleError , msg
        else:
            return None

    def getOutputFile( self, fileName ):
        """
        @param fileName:
        @type fileName: String
        @return: the content of a output file as a string
        @rtype: string
        @raise exception: 
        """
        if self.jobState:
            if self._hasRun:
                return self.jobState.getOutputFile( fileName )
            else:
                msg = "try to get result but the job had not run"
                raise MobyleError , msg
        else:
            return None  
        
        
    def isLocal( self ):
        """
        
        """
        if self.jobState:
                return self.jobState.isLocal()

    def getStatus(self):
        """
        @return: the status of the job
        @rtype: L{Mobyle.Status.Status} instance 
        """
        if self.jobState:
            return utils_getStatus( self.jobState.getID() )
        else:
            return  None 

    def isFinished(self):
        """
        @return: True if the job is finished, False Otherwise
        @rtype: boolean
        """
        if self.jobState:
            sm = StatusManager()
            status = sm.getStatus( self.jobState.getDir() )
            return status.isEnded()
        else:
            return None

    def getCommandLine(self):
        """
        @return: the Command line
        @rtype: string
        """
        if self.jobState:
            if self._hasRun:
                return self.jobState.getCommandLine()
            else:
                msg = "try to get the command but the job had not run"
                raise MobyleError , msg
        else:
            return None

    def getDataPrompt(self , paramName ):
        """
        @return: the prompt for an In/Output parameter
        @rtype: string
        """
        if self.jobState:
            if self._hasRun:
                return self.jobState.getPrompt( paramName )
            else:
                msg = "try to get the command but the job had not run"
                raise MobyleError , msg
        else:
            return None
    
    
    def getStdout(self):
        """
        @return: the content of the job stdout as a string
        @rtype: string
        @raise MobyleError: if the job is not finished raise a L{MobyleError}
        """
        if self.jobState:
            if self._hasRun:
                return self.jobState.getStdout()
            else:
                msg = "try to get the job stdout, but the job had not run"
                raise MobyleError , msg
        else:
            return None
    

    def getStderr(self):
        """
        @return: the content of the job stderr as a string
        @rtype: string
        @raise MobyleError: if the job is not finished raise a L{MobyleError}
        """
        if self.jobState:
            return self.jobState.getStderr()
        else:
            return None

    
    def open(self , fileName ):
        """
        return an file object if the file is local or a file like object if the file is distant
        we could apply the same method on this object: read(), readline(), readlines(), close(). (unlike file the file like object doesn't implement an iterator).
        @param fileName: the name of the file (given by getResults).
        @type fileName: string
        @return: a file or file like object, or None if the job isn't ran.
        """
        if self.jobState:
            return self.jobState.open( fileName )
        else:
            return None



    def getArgs(self):
        """
        read the parameters in the .index.xml file and return a dictionary containig these parameters
        @return: the parameters of a job
        @rtype: dictionary
        """
        if self.jobState:
            return self.jobState.getArgs()
        else:
            return None

        
    def _logError( self , userMsg = None , logMsg = None ):
       
        
        if userMsg:
            sm = StatusManager ()
            sm.setStatus( self.getDir() , Status( code = 5 , message = userMsg ) )

        if  logMsg :
            self.m_log.error( "%s/%s : %s" %( self._service.getName() ,
                                           self._job.getKey() ,
                                           logMsg
                                           )
                         )


        

