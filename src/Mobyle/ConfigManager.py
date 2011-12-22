########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under LGPLv2 Licence. Please refer to the COPYING.LIB document.        #
#                                                                                      #
########################################################################################


import logging 
import sys
import os 
import re
import types


MOBYLEHOME = None
if os.environ.has_key('MOBYLEHOME'):
    MOBYLEHOME = os.environ['MOBYLEHOME']
if not MOBYLEHOME:
    sys.exit('MOBYLEHOME must be defined in your environment')

if ( MOBYLEHOME ) not in sys.path:
    sys.path.append( MOBYLEHOME )
if ( os.path.join( MOBYLEHOME , 'Src' ) ) not in sys.path:    
    sys.path.append( os.path.join( MOBYLEHOME , 'Src' ) )

from Dispatcher import DefaultDispatcher
from Mobyle.MobyleError import MobyleError , ConfigError

MOBYLEHTDOCS = None

class MetaSingleton(type):
    def __init__(cls , name , bases , classdict ):    
        cls._ref = None

    def __call__(cls , *args , **kwargs ):
        if cls._ref:
            return cls._ref
        else:
            instance = cls.__new__(cls,  *args , **kwargs )
            instance.__init__( *args , **kwargs )
            cls._ref = instance
            return  instance
        
        
class Config( object ):
    """
    this class is designed as the singleton pattern
    (ref: Programmation Python , Tarek Ziade .p 483).
    there is only one instance at once.
    this class parse the file local/Config/Config.py
    raise error fix default values raise error if needed. 
    all other Mobyle classes must use this class to access
    to a configuration information. 
    """
    
    __metaclass__ = MetaSingleton
    
    def __init__(self):
            self.__version = None
            import Local.Config.Config
            import Local.Config.Execution
            #############################
            #
            # logging
            #
            ##############################
            
            try:
                self._logdir = Local.Config.Config.LOGDIR
            except AttributeError:
                self._logdir = "/dev/null"
                msg = "LOGDIR not found in  Local/Config/Config.py"
                print >> sys.stderr,  "%s . It sets to %s" % ( msg , self._logdir ) 

            self.log = logging.getLogger('Mobyle.Config')
            self.log.propagate = False
            try:
                defaultHandler = logging.FileHandler( os.path.join( self._logdir , 'error_log' ) , 'a')
            except :
                print >> sys.stderr , " WARNING : can't access to logfile. Logs will redirect to /dev/null"
                defaultHandler = logging.FileHandler( '/dev/null' , 'a' )

            defaultFormatter = logging.Formatter(
                '%(name)-10s : %(levelname)-8s : L %(lineno)d : %(asctime)s : %(message)s' ,
                '%a, %d %b %Y %H:%M:%S'
                )

            #defaultHandler.setLevel( logging.DEBUG )
            defaultHandler.setFormatter( defaultFormatter )
            self.log.addHandler( defaultHandler )

            if  os.path.exists( MOBYLEHOME ):
                self._mobylehome = os.path.realpath( MOBYLEHOME )
            else:
                raise MobyleError , "MOBYLEHOME is not defined"
  
            ######################
            #
            # Mandatory values
            #
            ######################

            try: #old style config
                if os.path.exists( Local.Config.Config.DOCUMENT_ROOT ):
                    self._mobyle_htdocs = os.path.realpath( Local.Config.Config.DOCUMENT_ROOT )
                else:
                    msg = "DOCUMENT_ROOT: %s does not exist" % Local.Config.Config.DOCUMENT_ROOT
                    self.log.error( msg )
                    raise ConfigError , msg
            except AttributeError: 
                if MOBYLEHTDOCS: #define by new installer
                    if os.path.exists( MOBYLEHTDOCS ):
                        self._mobyle_htdocs = os.path.realpath( MOBYLEHTDOCS )
                    else: #never happen ?
                        msg = "bad installation option --install-htdocs : %s no such directory " % MOBYLEHTDOCS
                        raise ConfigError , msg
                else:
                    try: #define in Config.py witout installer but with new style config
                        if os.path.exists( Local.Config.Config.MOBYLEHTDOCS ):
                            self._mobyle_htdocs = os.path.realpath( Local.Config.Config.MOBYLEHTDOCS )
                        else:
                            msg = "MOBYLEHTDOCS: %s no such directory" % Local.Config.Config.MOBYLEHTDOCS
                            self.log.error( msg )
                            raise ConfigError , msg
                    except AttributeError:
                        msg = "error during installation or configuration MOBYLEHTDOCS not found"
                        self.log.error( msg )
                        raise ConfigError , msg
                
            try:
                self._root_url = Local.Config.Config.ROOT_URL.strip( '/' )
            except AttributeError:
                msg = "ROOT_URL not found in Local/Config/Config.py"
                self.log.error( msg )
                raise ConfigError , msg
            
            try:
                self._cgi_prefix = Local.Config.Config.CGI_PREFIX.strip( '/' )
            except AttributeError:
                    msg = "CGI_PREFIX not found in Local/Config/Config.py"
                    self.log.error( msg )
                    raise ConfigError , msg
            try:
                self._htdocs_prefix = Local.Config.Config.HTDOCS_PREFIX.strip( '/' )
            except AttributeError:
                    msg = "HTDOCS_PREFIX not found in Local/Config/Config.py" 
                    self.log.error( "HTDOCS_PREFIX not found in Local/Config/Config.py" )
                    raise ConfigError , msg
                    
            if  self._htdocs_prefix is not None :
                    self._portal_prefix = self._htdocs_prefix + '/portal'
                    self._portal_prefix = self._portal_prefix.lstrip( '/' )
                    self._portal_path = os.path.realpath( os.path.join( self._mobyle_htdocs , 'portal' ) )
            
            ######################
            #
            #  default values
            #
            #######################
            
            self._debug = 0
            self._particular_debug = {}
            
            self._accounting = False
            self._session_debug = None
            self._status_debug = False
            
            if self._htdocs_prefix:
                self._repository_url = "%s/%s/%s" % ( self._root_url , self._htdocs_prefix , 'data' )
            else:
                self._repository_url = "%s/%s" % ( self._root_url , 'data' )
                
            self._results_url = "%s/%s" % ( self._repository_url , 'jobs' )
            self._user_sessions_url = "%s/%s" % ( self._repository_url , 'sessions' )
            self._servers_url = "%s/%s/%s" % ( self._repository_url , 'services' , 'servers' )
            
            self._repository_path = os.path.realpath( os.path.join( self._mobyle_htdocs , 'data' ) ) 
            self._services_path = os.path.realpath( os.path.join( self._repository_path , 'services' ) )
            self._servers_path = os.path.realpath( os.path.join( self._services_path, 'servers' ) )
            self._index_path = os.path.realpath( os.path.join( self._services_path ,'index' ) )
            
            self._results_path = os.path.realpath( os.path.join( self._repository_path , 'jobs' ) )
            self._user_sessions_path = os.path.realpath( os.path.join( self._repository_path , 'sessions' ) )
            #OPENID
            self._openidstore_path = os.path.realpath( os.path.join( self._repository_path , 'openidstore' ) )
            
            self._binary_path = []  
            self._format_detector_cache_path = None
            
            self._databanks_config = {}
            
            self._dns_resolver = False 
            self._opt_email = False
            self._particular_opt_email = {}
            
            self._anonymous_session = "captcha"
            self._authenticated_session = 'email'

            #OPENID
            self._openid = False
            
            self._refresh_frequency = 240
            
            self._dont_email_result = False
            
            self._filelimit = 2147483648     #  2 Gib
            self._sessionlimit = 52428800    # 50 Mib
            self._previewDataLimit = 1048576 #  1 Mib
            self._simultaneous_jobs = 1
            
            self._result_remain = 10 # in day
            
            self._lang = 'en'
            self._email_delay = 20
            
            self._dataconverter = {}
            
            self._execution_system_alias  = { 'SYS' : Local.Config.Execution.SYSConfig() }
            self._dispatcher = DefaultDispatcher( { 'DEFAULT'  : ( self._execution_system_alias[ 'SYS' ] , '' ) } )
            
            self._services_deployment_include = { 'programs' : [ '*' ] ,
                                                 'workflows' : [ '*' ] ,
                                                 'viewers'   : [ '*' ] ,
                                                 }
            self._services_deployment_exclude = { 'programs' : [] ,
                                                 'workflows' : [] ,
                                                 'viewers'   : [] ,
                                                 }
            
            self._disable_all = False
            self._disabled_services = []
            
            self._authorized_services = {}
            self._all_portals = {}
            self._exported_services = []
            
            
            try:
                self._accounting = Local.Config.Config.ACCOUNTING
            except AttributeError:
                self.log.info( "ACCOUNTING not found in  Local/Config/Config.py, set ACCOUNTING= %s" %self._accounting )
            try:
                self._session_debug = Local.Config.Config.SESSION_DEBUG
            except AttributeError:
                pass
            try:
                self._status_debug = Local.Config.Config.STATUS_DEBUG
            except AttributeError:
                pass
            ######################
            #
            #  Directories
            #
            ######################
            
            ## in htdocs ##
            
            
            #OPENID
            try:
                if os.path.exists( Local.Config.Config.OPENIDSTORE_PATH ):
                    self._openidstore_path = os.path.realpath( Local.Config.Config.OPENIDSTORE_PATH )
                else:
                    msg = "OPENIDSTORE_PATH: %s does not exit" % Local.Config.Config.OPENIDSTORE_PATH
                    self.log.error( msg )
                    raise ConfigError , msg
            except AttributeError, err:
                self.log.debug( "OPENIDSTORE_PATH not found in Local/Config/Config.py default value used : " +str( self._openidstore_path) )

 
            ## out web ##
            self._admindir =  os.path.join( self._results_path , 'ADMINDIR' )
            
            try:
                binary_path = []
                for path in Local.Config.Config.BINARY_PATH:
                    binary_path.append( path )
                self._binary_path  = binary_path
            except AttributeError:
                self.log.warning( "BINARY_PATH not found in Local/Config/Config.py the default web server path will be used" )
                
            try:
                if os.path.exists( Local.Config.Config.FORMAT_DETECTOR_CACHE_PATH ):
                    self._format_detector_cache_path = os.path.realpath( Local.Config.Config.FORMAT_DETECTOR_CACHE_PATH )
                else:
                    msg = "FORMAT_DETECTOR_CACHE_PATH: %s does not exit" % Local.Config.Config.FORMAT_DETECTOR_CACHE_PATH
                    self.log.error( msg )
                    raise ConfigError , msg
            except AttributeError:
                pass
                
            try:
                self._databanks_config = Local.Config.Config.DATABANKS_CONFIG
            except AttributeError:
                self.log.info( "No databanks are found in Local/Config/Config.py" )
                    
                    
            
            #######################
            #
            #    debug
            #
            #######################

            try:
                debug = Local.Config.Config.DEBUG
                if debug >= 0 or debug <= 3:
                    self._debug = debug
                else:
                    self.log.warning( "DEBUG must be >= 0 and <= 3 I found DEBUG =%s, DEBUG is set to %i" % ( debug , self._debug ) ) 
            except AttributeError:
                self.log.info( "DEBUG not found in Local/Config/Config.py, DEBUG is set to %i" % self._debug )

            try:
                self._particular_debug = Local.Config.Config.PARTICULAR_DEBUG
            except AttributeError:
                self.log.info( "PARTICULAR_DEBUG not found in Local/Config/Config.py" )
                                        
            #######################
            #
            #  Mail
            #
            #######################

            try:
                if type( Local.Config.Config.MAINTAINER ) == types.ListType or type( Local.Config.Config.MAINTAINER ) == types.TupleType :
                    self._maintainer = Local.Config.Config.MAINTAINER
                else:
                    self._maintainer = [ Local.Config.Config.MAINTAINER ]
                    
                if type( Local.Config.Config.HELP ) == types.ListType or type( Local.Config.Config.HELP ) == types.TupleType :    
                    self._help = " , ".join( Local.Config.Config.HELP )
                else:
                    self._help = Local.Config.Config.HELP

                self._mailhost = Local.Config.Config.MAILHOST
            except AttributeError, err:
                msg = str(err).split()[-1] + "not found in Local/Config/Config.py"
                self.log.error( msg )
                raise ConfigError , msg         
                
            try:
                self._sender = Local.Config.Config.SENDER
            except AttributeError, err:
                self._sender = self._help
                self.log.info( "SENDER not found in  Local/Config/Config.py , set SENDER to HELP ")
                
            try:
                self._dns_resolver = Local.Config.Config.DNS_RESOLVER
            except AttributeError:
                self.log.info( "DNS_RESOLVER not found in  Local/Config/Config.py, set DNS_RESOLVER to False" )

            #######################
            #
            # Statistics
            #
            #######################

            #GOOGLE ANALYTICS
            try:
                self._GAcode = Local.Config.Config.GACODE
            except AttributeError:
                self._GAcode = None

            #######################
            #
            # Welcome page configuration
            #
            #######################

            try:
                self._welcome_config = Local.Config.Config.WELCOME_CONFIG
            except AttributeError:
                self._welcome_config = {}
                
            #######################
            #
            # Portal customization
            #
            #######################
            
            try:
                self._custom_portal_header = Local.Config.Config.CUSTOM_PORTAL_HEADER
            except AttributeError:
                self._custom_portal_header = None

            try:
                self._custom_portal_footer = Local.Config.Config.CUSTOM_PORTAL_FOOTER
            except AttributeError:
                self._custom_portal_footer = None

                
            #######################
            #
            #     Authentication
            #
            #######################

            #OPENID
            try:
                self._openid = Local.Config.Config.OPENID
            except AttributeError:
                self.log.info("OPENID not found in Local/Config/Config.py")

            try:
                self._opt_email = Local.Config.Config.OPT_EMAIL
            except AttributeError:
                self.log.info( "OPT_EMAIL not found in  Local/Config/Config.py, set OPT_EMAIL to %s" % self._opt_email )
                               
            try:
                self._particular_opt_email = Local.Config.Config.PARTICULAR_OPT_EMAIL
            except AttributeError:
                self.log.info( "PARTICULAR_OPT_EMAIL not found in  Local/Config/Config.py, use OPT_EMAIL for all services" )
                
            try:
                self._anonymous_session = Local.Config.Config.ANONYMOUS_SESSION
                try:
                    self._anonymous_session = self._anonymous_session.lower()
                except AttributeError:
                    self._anonymous_session = "captcha"
                    self.log.warning( "ANONYMOUS_SESSION have a wrong value: " + str( Local.Config.Config.ANONYMOUS_SESSION ) + " , set to \"%s\"" %self._anonymous_session)
               
                if self._anonymous_session == "yes" or self._anonymous_session == "y":
                    self._anonymous_session = "yes"
                elif self._anonymous_session == "no" or self._anonymous_session == "n":
                    self._anonymous_session = "no"
                elif self._anonymous_session != "captcha":
                    self._anonymous_session = "captcha"
                    self.log.warning( "ANONYMOUS_SESSION have a wrong value: " + str( Local.Config.Config.ANONYMOUS_SESSION ) + " , set to \"captcha\"" )

            except AttributeError:
                self.log.info( "ANONYMOUS_SESSION not found in  Local/Config/Config.py, set to  default value: \"%s\"" %self._anonymous_session )
            try:
                self._authenticated_session = Local.Config.Config.AUTHENTICATED_SESSION
                    
                if self._authenticated_session not in ( "email" ,"no" ,"yes" ):
                    self.log.warning( "AUTHENTICATED_SESSION have a wrong value: %s set to \"%s\""%( Local.Config.Config.AUTHENTICATED_SESSION ,
                                                                                                      self._authenticated_session ) )
                        
                if self._anonymous_session == "no" and not self._authenticated_session :
                    msg = "anonymous session AND authenticated session are disabled. you can't disabled both"
                    self.log.error( msg )
                    raise ConfigError , msg
                
            except AttributeError , err :
                self.log.info( "AUTHENTICATED_SESSION not found in  Local/Config/Config.py , set to default value: \"%s\"" %self._authenticated_session )         
                
            try:
                self._refresh_frequency = Local.Config.Config.REFRESH_FREQUENCY
            except AttributeError:
                self.log.info( "REFRESH_FREQUENCY not found in Local/Config/Config.py, set to %s" % self._refresh_frequency )               
                
            ########################
            #
            #      results
            #
            ########################
               
            try:
                self._dont_email_result = Local.Config.Config.DONT_EMAIL_RESULTS
            except AttributeError:
                self.log.info( "DONT_EMAIL_RESULTS not found in  Local/Config/Config.py, set DONT_EMAIL_RESULTS to %s" %self._dont_email_result)

            try:
                self._maxmailsize = Local.Config.Config.MAXMAILSIZE
            except AttributeError:
                if not self._dont_email_result :
                    self.log.info("MAXMAILSIZE not found in  Local/Config/Config.py but DONT_EMAIL_RESULTS is False, I set MAXMAILSIZE = 2 Mo")
                    self._maxmailsize = 2097152 
                else:
                    self._maxmailsize = None

            try:
                self._filelimit = int( Local.Config.Config.FILELIMIT )
            except AttributeError:
                self.log.info( "FILELIMIT not found in  Local/Config/Config.py, set FILELIMIT to %d Gib" %( self._filelimit / 1073741824 ) )
            except ValueError:
                msg = "FILELIMIT have an invalid value : %s .\nIt must be an integer" % self._filelimit 
                self.log.error( msg )
                raise ConfigError , msg
 
            try:
                self._sessionlimit = int( Local.Config.Config.SESSIONLIMIT )
            except AttributeError:
                self.log.info( "SESSIONLIMIT not found in  Local/Config/Config.py, set SESSIONLIMIT to %d Mib" %( self._sessionlimit / 1048576 ) )
            except ValueError:
                msg = "SESSIONLIMIT have an invalid value : %s .\nIt must be an integer" % self._sessionlimit 
                self.log.error( msg )
                raise ConfigError , msg

            try:
                self._previewDataLimit = int( Local.Config.Config.PREVIEW_DATA_LIMIT )
            except AttributeError:
                self.log.info( "PREVIEW_DATA_LIMIT not found in  Local/Config/Config.py, set PREVIEW_DATA_LIMIT to %d Mib"%( self._previewDataLimit / 1048576 ) )
            except ValueError:
                msg = "PREVIEW_DATA_LIMIT have an invalid value : %s .\nIt must be an integer" % self._sessionlimit 
                self.log.error( msg )
                raise ConfigError , msg

            try:
                self._result_remain = int( Local.Config.Config.RESULT_REMAIN )
            except AttributeError:
                self.log.info( "RESULT_REMAIN not found in  Local/Config/Config.py, set RESULT_REMAIN to %d days" %( self._result_remain ))
            except ValueError:
                msg = "RESULT_REMAIN have an invalid value : %s .\nIt must be an integer" % Local.Config.Config.RESULT_REMAIN
                self.log.error( msg )
                raise ConfigError , msg
            
            try:
                self._simultaneous_jobs = int( Local.Config.Config.SIMULTANEOUS_JOBS )
                if self._simultaneous_jobs < 0 :
                    msg = "SIMULTANEOUS_JOBS have an invalid value : %s .\nIt must be a positive or null integer" % Local.Config.Config.SIMULTANEOUS_JOBS
                    self.log.error( msg )
                    raise ConfigError , msg
            except AttributeError:
                self.log.info( "SIMULTANEOUS_JOBS not found in  Local/Config/Config.py, set SIMULTANEOUS_JOBS to %d " %( self._simultaneous_jobs ))
            except ValueError:
                msg = "SIMULTANEOUS_JOBS have an invalid value : %s .\nIt must be a positive or null integer" % Local.Config.Config.SIMULTANEOUS_JOBS
                self.log.error( msg )
                raise ConfigError , msg   
            #############################
            #
            #       CONVERTER
            #
            #############################
                       
            try:
                self._dataconverter = Local.Config.Config.DATA_CONVERTER
                for dtype in Local.Config.Config.DATA_CONVERTER:
                    self._dataconverter[ dtype ] = Local.Config.Config.DATA_CONVERTER[ dtype ]
            except AttributeError:
                pass

            ##############################
            #
            #      Misc
            #
            ##############################


            try:
                self._lang = Local.Config.Config.LANG
            except AttributeError:
                self.log.info( "LANG not found in  Local/Config/Config.py, set LANG to %s" % self._lang)

            try:
                self._email_delay = Local.Config.Config.EMAIL_DELAY
            except AttributeError:
                try:
                    self._email_delay = Local.Config.Config.TIMEOUT
                    self.log.info( "TIMEOUT is deprecated and replaced by EMAIL_DELAY, set EMAIL_DELAY to %d" % self._email_delay)
                except AttributeError:
                    self.log.info( "EMAIL_DELAY not found in  Local/Config/Config.py, set EMAIL_DELAY to %d" % self._email_delay)

            ##############################
            #
            #      BATCH
            #
            ##############################
            try:
                self._execution_system_alias = Local.Config.Config.EXECUTION_SYSTEM_ALIAS
            except AttributeError:
                msg = "EXECUTION_SYSTEM_ALIAS not found in  Local/Config/Config.py, it is set to %s" % self._execution_system_alias.values()[0]
                self.log.warning( msg ) 
                  
            if not self._execution_system_alias:
                self._execution_system_alias = { 'SYS' : Local.Config.Execution.SYSConfig() }
                msg = "EXECUTION_SYSTEM_ALIAS in Local/Config/Config.py is empty. it is fill with %s" % self._execution_system_alias[ 'SYS' ]
                self.log.warning( msg ) 
                
            try:
                self._dispatcher = Local.Config.Config.DISPATCHER
            except AttributeError:
                default_alias_name , default_alias = self._execution_system_alias.items()[0]
                msg = "DISPATCHER not found in  Local/Config/Config.py, it is set to { 'DEFAULT' : %s }" % default_alias_name
                self.log.warning( msg )  
            
            self._revert_alias = dict( [ ( config , alias ) for alias , config in self._execution_system_alias.items() ] )
                

            try:
                self._default_Q = Local.Config.Config.DEFAULT_Q
            except AttributeError:
                self._default_Q = 'mobyle'
                self.log.info( "DEFAULT_Q not found in  Local/Config/Config.py. it is set to mobyle" )

            try:
                self._particular_Q  = Local.Config.Config.PARTICULAR_Q
            except AttributeError:
                self.log.info( "PARTICULAR_Q not found in  Local/Config/Config.py" )

#            try:
#                self._Qproperties = Local.Config.Config.Q_PROPERTIES
#            except AttributeError:
#                self.log.info( "Q_PROPERTIES not found in  Local/Config/Config.py" )

            ##########################
            #
            # services publication
            #
            ###########################
            try:
                self._services_deployment_exclude.update( Local.Config.Config.LOCAL_DEPLOY_EXCLUDE )
            except ( AttributeError , NameError ):
                self.log.info( "LOCAL_DEPLOY_EXCLUDE not found in  Local/Config/Config.py" )
                
            try:
                self._services_deployment_include.update( Local.Config.Config.LOCAL_DEPLOY_INCLUDE )
            except ( AttributeError , NameError ):
                self.log.info( "LOCAL_DEPLOY_INCLUDE not found in  Local/Config/Config.py" )


            #############################
            #
            # disabled service
            #
            #############################

            try:
                self._disable_all = Local.Config.Config.DISABLE_ALL
            except AttributeError:
                msg = "DISABLE_ALL not found in  Local/Config/Config.py,set to %s" % self._disable_all
                self.log.info( msg )
            try:
                self._disabled_services = Local.Config.Config.DISABLED_SERVICES
            except AttributeError:
                msg = "DISABLED_SERVICES not found in  Local/Config/Config.py,"
                self.log.info( msg )
                
            #########################################
            #
            # restriction services access
            #
            #########################################

            try:
                self._authorized_services = Local.Config.Config.AUTHORIZED_SERVICES
            except AttributeError:
                self.log.info( "AUTHORIZED_SERVICES not found in  Local/Config/Config.py" )
            
            #########################################
            #
            # Grid aspects
            #
            #########################################    
            
            self._portal_name = "anonymous"
            try:
                self._portal_name = Local.Config.Config.PORTAL_NAME
            except AttributeError:
                pass

            try:
                self._all_portals = Local.Config.Config.PORTALS 
                for portal in self._all_portals .keys():
                    self._all_portals[ portal ][ 'url' ] = self._all_portals[ portal ][ 'url' ].rstrip( '/')
                    self._all_portals[ portal ][ 'repository' ] = "%s/%s" % ( self._all_portals[ portal ][ 'repository' ].rstrip( '/') ,
                                                                             'data' )
                    #self._all_portals[ portal ][ 'jobsBase' ] = self._all_portals[ portal ][ 'jobsBase' ].rstrip( '/')
            except KeyError , err:
                msg = "error PORTALS : %s is not properly defined : %s" % ( portal , err )
                self.log.warning( msg )
                try:
                    del self._all_portals[ portal ]
                except KeyError:
                    pass
                self.log.warning( " the portal: %s will not be imported" % portal )
            except AttributeError:
                pass

            try:
                self._exported_services = Local.Config.Config.EXPORTED_SERVICES
            except AttributeError:
                self.log.info( "EXPORTED_SERVICES not found in  Local/Config/Config.py" )
            



    ###############################
    #
    #    accessors
    #
    ##############################
    def version( self ):
        """
        @return: the version number of this Mobyle instance
        @rtype: 
        """
        return self.__version 
    
    def debug( self , jobName = None ):
        """
        Returns the debug level for a job or the default debug level if jobName is not specified
        @param jobName:
        @type jobName: string
        @return: an int >=0 and <= 3
        @rtype: int
        """
        try:
            debug = self._particular_debug[ jobName ]
        except KeyError:
            debug = self._debug
        if debug < 0 or debug > 3:
            if jobName is None:
                msg =" DEBUG must be >= 0 and <= 3 I found DEBUG =%i, DEBUG is set to %i" % ( debug , self._debug )
            else:
                msg = jobName + " debug must be >= 0 and <= 3 I found %i,  PARTICULAR_DEBUG[ '%s' ] is set it to %i" % ( debug ,
                                                                                                                         jobName , 
                                                                                                                         self._debug )
            self.log.warning( msg )
        return debug
    
    
    def mobylehome( self ):
        """
        @return: the absolute path to home of the project
        @rtype: string
        """
        return self._mobylehome
    
    
    def document_root( self ):
        """
        @return: the absolute path to the mobyle htdocs directory
        @rtype: string
        """
        return self._mobyle_htdocs
    
    
    def root_url( self ):
        """
        @return: the base url of the web server
        @rtype: string
        """
        return self._root_url


    def results_url( self ):
        """
        @return: the complete url of the jobs
        @rtype: string
        """
        return self._results_url

    def results_path( self ):
        """
        @return: the directory absolute path  where are located the jobs
        @rtype: string
        """
        return self._results_path
    
    def admindir(self):
        """
        @return: the absolute path of the ADMINDIR
        @rtype: string
        """
        return self._admindir

    def servers_url( self ):
        """
        @return: the base url of the service definitions
        @rtype: string
        """
        return self._servers_url

    def servers_path( self ):
        """
        @return: the directory absolute path  where are located the services
        @rtype: string
        """
        return self._servers_path
    
    def services_path( self ):
        """
        @return: the directory absolute path  where are located the services
        @rtype: string
        """
        return self._services_path
    
    def repository_path( self ):
        """
        @return: the absolute path where are located the services, jobs, sessions ... 
        @rtype: string
        """
        return self._repository_path
    
    def repository_url( self ):
        """
        @return: the url where are located the services, index , jobs, ... 
        @rtype: string
        """
        return self._repository_url


    def index_path( self ):
        """
        @return: the directory absolute path  where are located the indexes for this portal.
        @rtype: string
        """
        return self._index_path
    
    def binary_path( self ):
        """
        @return: the list of path where binaries must be search
        @rtype: list of strings
        """
        return self._binary_path
    

    def format_detector_cache_path( self ):
        """
        @return: the absolute path where the invalid sequences and alignment are dumped for analysis
        @rtype: string
        """
        return self._format_detector_cache_path


    def user_sessions_path( self ):
        """
        @return: the directory absolute path  where are located the sessions
        @rtype: string
        """
        return self._user_sessions_path
    
    def user_sessions_url( self ):
        """
        @return: the complete url of the sessions
        @rtype: string
        """
        return self._user_sessions_url 
    
    def log_dir( self ):
        """
        @return: the absolute path where located the log files
        @rtype: string
        """
        return self._logdir
       
    
    def portal_url( self , relative = False ):
        """
        @param relative:
        @type relative: boolean
        @return: if relative return the relative url of the portal otherwise return the absolute 
                 url of the portal.
        @rtype: string
        """
        if relative:
            return self._portal_prefix
        else:
            return "%s/%s" % ( self._root_url , self._portal_prefix )
    
    def portal_path(self):
        """
        @return: the absolute path to the portal
        @rtype: string
        """
        return  self._portal_path
    
    
    def cgi_url( self ):
        """
        @return: the absolute url to the cgis
        @rtype: string
        """
        return "%s/%s" % ( self._root_url , self._cgi_prefix )
    

    def getDatabanksConfig(self):
        """
        @return: the list of databanks
         along with their typing information and label
        @rtype: dictionary
        """
        return self._databanks_config
        
    
    def maintainer( self ):
        """
        @return: the email address of the Mobyle server  maintainer
        @rtype: string
        """
        return self._maintainer

    def mailHelp( self ):
        """
        @return: The email address to the hot line for this Mobyle server
        @rtype: string
        """
        return self._help
    
    
    def sender( self ):
        """
        the sender address is used as From: for mail sent by mobyle
        - notification of long job
        - results
        - session confirmation  
        @return: the sender email address ( From: ) of this Mobyle server
        @rtype: string
        """
        return self._sender
    

    def mailhost( self ):
        """
        @return: the mail transfert agent used to send emails
        @rtype: string
        """
        return self._mailhost


    def opt_email( self , portalid = None ):
        """
        @return: True if the user email is not mandatory to run a job, False otherwise
        @rtype: Boolean
        """
        if portalid is None:
            return self._opt_email
        else:
            if portalid.find( '.' ) == -1:
                portalid = "local.%s"%portalid
            try:
                return self._particular_opt_email[ portalid ]
            except KeyError:
                return self._opt_email 

    #OPENID
    def openid( self ):
        """
        @return: True if openid authentication is supported , False otherwise
        @rtype: boolean
        """
        return self._openid

    #OPENID
    def openidstore_path( self ):
        """
        @return: the directory absolute path  where is located the openid store
        @rtype: string
        """
        return self._openidstore_path
            
    
    def anonymousSession( self ):
        """
        @return: 
          - 'no'       if the anonymous sessions are not allowed.
          - 'yes'      if the anonymous sessions are allowed, without any restrictions.
          - 'captcha'  if the anonymous sessions are allowed, with a captcha challenge.
        @rtype: string
        """
        return self._anonymous_session
    
    
    def authenticatedSession( self ):
        """
        @return: 
          - 'no'     if authenticated session are not allowed.
          - 'yes'    if authenticated session are allowed and activated without any restriction.
          - 'email'  if authenticated session are allowed but an email confirmation is needed to activate it.
        @rtype: string
        """
        return self._authenticated_session

    def refreshFrequency( self ):
        """
        @return: portal refresh frequency, in seconds
        @rtype: integer
        """
        return self._refresh_frequency
    
    
    def dnsResolver( self ):
        """
        @return: True if the user email domain name is checked to have a mail server , False otherwise 
        @rtype: boolean
        """
        return self._dns_resolver

    
    def mailResults( self ):
        """
        @return: dont_email_result , mailmaxsize in a tuple
        @rtype: ( boolean , int )
        """
        return ( self._dont_email_result , self._maxmailsize )


    def remainResults( self ):
        """
        @return: how long ( in days ) the results files remains on the server.
        @rtype: int
        """
        return self._result_remain

    def simultaneous_jobs( self ):
        """
        @return: how many "indentical" jobs are allowed to be submit in same time.
        "indentical" jobs means same email, same IP, same commandline.
        @rtype: int
        """
        return self._simultaneous_jobs
       
     
    def lang( self ):
        """
        @return: The default language used by this Mobyle server (used to internationalise the form) 
        (2 letter code )(default = "en")
        @rtype: string
        """
        return self._lang


    def filelimit( self ):
        """
        @return: the max size for one file generated by a service ( in byte ). 
        @rtype: int
        """
        return self._filelimit

    def sessionlimit( self ):
        """
        @return: the max size for a session directory ( in byte )
        @rtype: int
        """
        return self._sessionlimit
    
    def previewDataLimit( self ):
        """
        @return: the max size for a result to be preview in job result ( in Byte ).
        @rtype: int
        """
        return self._previewDataLimit   

    def dataconverter(self, datatype):
        """
        @param datatype: the name of a datatype as found in the xml of services
        @type datatype: string
        @return: list of dataconverter insntance  for a given datatype
        """
        try:
            return self._dataconverter[ datatype ]
        except KeyError:
            return []
        
    def data_conversions(self):
        """
        data_conversions returns the list of conversion possibilities as a list of dictionnaries
        computed from the configured converters
        @type datatype: string
        @return: list of dataconverter insntance  for a given datatype
        """
        list = []
        for dts, entries in self._dataconverter.items():
            for entry in entries:
                for fts in entry.convertedFormat():
                    if fts[0] != fts[1]:
                        list.append({'dataType':dts, 'fromFormat':fts[0], 'toFormat':fts[1], 'using':entry.program_name})
        return list
    
    def email_delay( self ):
        """
        @return: the time during the father process wait its child  ( in sec ).
        @rtype: int 
        """
        return self._email_delay


    def getAliasFromConfig(self , config ):
        try:
            return self._revert_alias[ config ]
        except KeyError:
            raise ConfigError()
            
    def getExecutionConfigFromAlias(self , alias ):
        """
        @param alias: the symbolic name of a ExecutionConfig object in the Execution_CONFIG_ALIAS
        @type alias: string
        @return: the ExecutionConfig corresponding to the symbolic name alias
        @rtype: ExecutionConfig
        @raise KeyError: if alias doesn't match with any alias in Config.
        """
        try:
            return self._execution_system_alias[ alias ]
        except KeyError , err:
            raise err 
        
    def getDispatcher( self):
        """
        @return: a L{Dispatcher} 
        @rtype: a L{Dispatcher} instance
        """
        return self._dispatcher
        
        
    def accounting( self ):
        """
        @return: True if the accounting is on, False otherwise.
        @rtype: boolean
        """
        return self._accounting

    def session_debug( self ):
        """
        @return: the debug level for the session specifique logger. 
        if there is no level specify in Config, return None 
        @rtype: int
        """
        return self._session_debug
    
    def status_debug( self ):
        """
        @return: True if the debug log on status is on, False otherwise.
        @rtype: boolean
        """
        return self._status_debug
    
    def isDisabled( self , portalID = None ):
        """
        @param portalID: the portalID of a service. 
        The portalID is the portal name and service name separated by a dot like portal1.service1
        local means the local portal  
        @type: string
        @return: True if the service is disabled, False otherwise
        @rtype: boolean
        """
        
        if portalID is None:
            return self._disable_all
        else:
            if self._disable_all :
                return True
            else:
                pattern = self._disabled_services
                if pattern :
                    pattern = '|'.join( pattern )
                    pattern = pattern.replace('.' , '\.' )
                    pattern = pattern.replace('*' , '.*')
                    pattern = "^(%s)$" % pattern
                    auto = re.compile( pattern )
                else:
                    # by default if no pattern are specified all services are enabled
                    return False
                if auto.search( portalID ):
                    return True
                else:
                    return False





    def restrictedServices( self ):
        """
        @return: The list of service which have a restrictive access
        @rtype: list of strings
        """
        return self._authorized_services.keys()


    def isAuthorized( self , serviceName , addr = None ):
        """
        @param service: the name of the service
        @type service: type
        @param addr: the ip address to test. if addr is None the environment REMOTE_ADDR will be used
        @type addr: string
        @return: True if the user is authorized to used the service (based on IP), False otherwise.
        @rtype: boolean
        """
        if addr is None:
            try: 
                addr = os.environ[ 'REMOTE_ADDR' ]
            except KeyError:
                return True
        try:
            pattern = self._authorized_services[ serviceName ]
        except KeyError:
            # by default if no pattern are specified there is no restriction
            # to access to this service
            return True
        
        if pattern :
            pattern = '|'.join( pattern )
            pattern = pattern.replace('.' , '\.' )
            pattern = pattern.replace('*' , '.*')
            pattern = "^(%s)$" % pattern
            auto = re.compile( pattern )
        else:
            # by default if no pattern are specified there is no restriction
            # to access to this service
            return True
        
        if auto.search( addr ):
            return True
        else:
            return False

    def getPrivilegeTable( self ):
        """
        @return: a dict where keys are the service names and values a list of Ip mask which are authorized to access to this service
        @rtype: dict { string : [ strings ] }
        """
        return self._authorized_services


    def imported_services( self ):
        """
        @return: the urls of the services imported by this server
        @rtype: list of strings
        """
        return self._imported_services
    
    
    def exported_services( self ):
        """
        @return: the name of the services which are exported by this server
        @rtype: list of strings
        """
        return self._exported_services

    def portal_name( self ):
        """
        @return: the name of the portal within a MobyleNet federation
        @rtype: String
        """
        return self._portal_name
    
    
    def portals( self ):
        """
        @return: all the Mobyle portals belonging to the "Mobyle grid"
        @rtype: list of dictionaries  {     { 'server' : 'url of Mobyle server' ,
                                            'email' : 'the contact email of this server' }
                                        }
        """
        return self._all_portals
    
    
    def services_deployment_include(self, service_type = None ):
        """
        @param service_type: the type of the service to deploy
        @type service_type: string (for now the available keywords are 'programs' , 'workflows' and 'viewers'
        @return: the services deployment include masks list
        @rtype: list of strings
        """
        if service_type is None:
            return self._services_deployment_include
        else:
            try:
                return self._services_deployment_include[ service_type ]
            except KeyError:
                raise KeyError( "the '%s' service type is not handled by Mobyle" %service_type )
        
    
    
    def services_deployment_exclude(self, service_type = None ):
        """
        @param service_type: the type of the service to not deploy
        @type service_type: string (for now the available keywords are 'programs' , 'workflows' and 'viewers'
        @return: the services deployment exclude masks list
        @rtype: list of strings
        """
        if service_type is None:
            return self._services_deployment_exclude
        else:
            try:
                return self._services_deployment_exclude[ service_type ]
            except KeyError:
                raise KeyError( "the '%s' service type is not handled by Mobyle" %service_type )
        
    def GAcode(self):
        """
        @return: the Google Analytics code if a GA account is used
        @rtype: string or None
        """
        return self._GAcode
        
    def welcome_config(self):
        """
        @return: the custom welcome page configuration
        @rtype: dictionary with keys 'url' and 'format' (format can be html or atom for instance)
        """
        return self._welcome_config

    def custom_portal_header(self):
        """
        @return: the custom portal header
        @rtype: string containing an HTML chunk
        """
        return self._custom_portal_header
    
    def custom_portal_footer(self):
        """
        @return: the custom portal footer
        @rtype: string containing an HTML chunk
        """
        return self._custom_portal_footer
    
