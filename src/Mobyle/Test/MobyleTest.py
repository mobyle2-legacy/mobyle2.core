########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################




from Mobyle.ConfigManager import Config
import os
        
    
class ConfigTest(Config):

    def __init__(self):
        self.test_dir = '/tmp/test_Mobyle'
        self._logdir = "/dev/null" 
        self._mobylehome = os.environ[ 'MOBYLEHOME' ]
         
        self._root_url      = 'file://%s' % self.test_dir
        self._htdocs_prefix = ''
        self._mobyle_htdocs = self.test_dir
        self._cgi_prefix    = 'cgi-bin'
        self._portal_prefix = '/portal'
        
        self._repository_path = os.path.realpath( os.path.join( self._mobyle_htdocs , 'data' ) ) 
        self._services_path = os.path.realpath( os.path.join( self._repository_path , 'services' ) )
        self._servers_path = os.path.realpath( os.path.join( self._services_path, 'servers' ) )
        self._index_path = os.path.realpath( os.path.join( self._services_path ,'index' ) )
            
        self._results_path = os.path.realpath( os.path.join( self._repository_path , 'jobs' ) )
        self._user_sessions_path = os.path.realpath( os.path.join( self._repository_path , 'sessions' ) )
        self._portal_path = os.path.realpath( os.path.join( self._mobyle_htdocs , 'portal' ) )
        
        self._repository_url = "%s/%s" % ( self._root_url , 'data' )
        self._results_url = "%s/%s" % ( self._repository_url , 'jobs' )
        self._user_sessions_url = "%s/%s" % ( self._repository_url , 'sessions' )
        self._servers_url = "%s/%s/%s" % ( self._repository_url , 'services' , 'servers' )
        
#        self._debug = 0
#        self._particular_debug = {}
#        self._accounting = False
        self._session_debug = False
        self._status_debug = False
#        
#        self._binary_path = []  
#        self._databanks_config = {}
        self._dns_resolver = False 
#        self._opt_email = False
#        self._particular_opt_email = {}
#        self._anonymous_session = "captcha"
#        self._authenticated_session = 'email'
#        
#        self._openid = False
#        self._openidstore_path = os.path.join( self._mobyle_htdocs , 'data' , 'openidstore' ) 
#        
#        self._refresh_frequency = 240
#        self._dont_email_result = False
        self._filelimit = 2147483648     #  2 Gib
        self._sessionlimit = 52428800    # 50 Mib
        self._previewDataLimit = 1048576 #  1 Mib
#        self._result_remain = 10 # in day
        self._lang = 'en'
#        
#        self._email_delay = 20
#        self._maxmailsize = 2097152 
        self._maintainer = [ 'maintainer@nowhere.com' ]
        self._help = 'helpy@nowhere.com'
        self._mailhost = ''
        self._sender = 'sender@nowhere.com'
#        
        self._dataconverter = {}
#        self._execution_system_alias  = { 'SYS' : Local.Config.Execution.SYSConfig() }
#        self._execution_system_config = { 'DEFAULT' : self._execution_system_alias[ 'SYS'] }
#        self._revert_alias = dict( [ ( config , alias ) for alias , config in self._execution_system_alias.items() ] )
#        self._default_Q = 'default_q'
#        self._particular_Q = {}
#        self._programs_deployment_include = ['*']
#        self._programs_deployment_exclude = []
#        self._programs_deployment_order = [ 'include' , 'exclude' ]
#        self._disable_all = False
#        self._disabled_services =[]
#        self._authorized_services = {}
        self._all_portals = {}
#        self._exported_programs = []
#        self._admindir =  os.path.join( self._results_path , 'ADMINDIR' )
#        
#        self._GAcode = None
        
         
__configTest = ConfigTest()
Config._ref = __configTest

#disabling the loggers 
import logging
class NullHandler(logging.Handler):
    def emit(self, record):
        pass
    
null_handlers = [ NullHandler() ]
from Mobyle.MobyleLogger import MLogger
ml = MLogger()
logging.getLogger('Mobyle').handlers = null_handlers
logging.getLogger('Mobyle.Session').handlers = null_handlers
logging.getLogger('Mobyle.account').handlers = null_handlers
logging.getLogger('Mobyle.builder').handlers = null_handlers
logging.getLogger('Mobyle.access').handlers = null_handlers


from Mobyle import Registry
registry_test = Registry.Registry()
local = Registry.ServerDef( 'local' , 
                            'file://%s' % __configTest.portal_path() , 
                            __configTest._help , 
                            'file://%s' % __configTest.services_path() , 
                            'file://%s' % __configTest.results_path()
                             )
registry_test.addServer( local )
Registry.registry = registry_test


def find_exe(program):
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split( os.pathsep ):
            exe_file = os.path.join( path, program )
            if is_exe( exe_file ):
                return exe_file

    return None
