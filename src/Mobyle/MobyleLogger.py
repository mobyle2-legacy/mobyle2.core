########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.        #
#                                                                                      #
########################################################################################

import logging.handlers
import os.path

from Mobyle.ConfigManager import Config
_cfg = Config()

#===============================================================================
# memo logging level
#
# CRITICAL      50
# ERROR         40
# WARNING       30
# INFO          20
# DEBUG         10
# NOTSET         0
#===============================================================================


class MLogger( object ):

    ## if we don't use the singleton pattern
    ## only one instance of logger is created
    ## but there is as much handler instance  as we call
    ## the creation procedure thus the messages are replicated

    _ref = None

    def __new__( cls , child = False):

        if cls._ref is None:
            cls._ref = super( MLogger , cls ).__new__( cls )
   
            ########################
            #                      #
            #       Formatter      # 
            #                      #
            ########################

            defaultFormatter = logging.Formatter(
                '%(name)-10s : %(levelname)-8s : %(filename)-10s: L %(lineno)d : %(asctime)s : %(message)s' ,
                '%a, %d %b %Y %H:%M:%S'
                )

            accountFormatter = logging.Formatter(
                '%(asctime)s  %(message)s' ,
                '%a, %d %b %Y %H:%M:%S')

            accessFormatter = logging.Formatter(
                '%(asctime)s %(message)s',
                 '%a, %d %b %Y %H:%M:%S' , 
                )

            builderFormatter = logging.Formatter( '%(message)s' )

            sessionFormatter = logging.Formatter(
                 'L %(lineno)d : %(asctime)s : pid = %(process)d  : %(message)s' ,
                '%a, %d %b %Y %H:%M:%S'
                )                                
            
            ########################
            #                      #
            #        Handler       #
            #                      #
            ########################

            logdir = _cfg.log_dir()
            try:

                defaultHandler = logging.FileHandler( os.path.join( logdir , 'error_log') , 'a' )
            except IOError:
                defaultHandler = logging.FileHandler( '/dev/null' , 'a' )
            
            #defaultHandler.setLevel(logging.WARNING)
            defaultHandler.setLevel( logging.DEBUG )
            defaultHandler.setFormatter( defaultFormatter )
            try:
                accountHandler = logging.FileHandler( os.path.join( logdir , 'account_log') , 'a' )
            except IOError:
                accountHandler = logging.FileHandler( '/dev/null' , 'a' )
            #accountHandler.setLevel()
            accountHandler.setFormatter( accountFormatter )
            buildLog = os.path.join( logdir , 'build_log')
            if not child :
                try:          
                    builderHandler = logging.FileHandler( buildLog , 'a' )
                except IOError:
                    builderHandler = logging.FileHandler( '/dev/null' , 'a' )
                builderHandler.setLevel( logging.NOTSET )
                builderHandler.setFormatter( builderFormatter )
            try:
                accessHandler = logging.FileHandler( os.path.join( logdir , 'access_log')  , 'a' )
            except IOError:
                accessHandler = logging.FileHandler( '/dev/null' , 'a' )
            accessHandler.setLevel( logging.INFO )
            accessHandler.setFormatter( accessFormatter )


            mailHandler = logging.handlers.SMTPHandler( _cfg.mailhost(),
                                                        _cfg.sender() ,
                                                        _cfg.maintainer()  ,
                                                        '[ %s ] Mobyle problem' % _cfg.root_url()
                                                        )
            mailHandler.setLevel(logging.CRITICAL)

            try:
                infoSessionHandler = logging.FileHandler( os.path.join( logdir , 'error_log' ) , 'a' )
            except IOError:
                infoSessionHandler = logging.FileHandler( '/dev/null' , 'a' )
            infoSessionHandler.setLevel( logging.WARNING )
            infoSessionHandler.setFormatter( defaultFormatter )            
            try:
                session_log_level = _cfg.session_debug()
                if session_log_level is not None :
                    sessionHandler = logging.FileHandler( os.path.join( logdir , 'session_log') , 'a' )
                else:
                    sessionHandler = logging.FileHandler( '/dev/null' , 'a' )                                  
            except IOError:
                sessionHandler = logging.FileHandler( '/dev/null' , 'a' )
            
            sessionHandler.setLevel( session_log_level if  session_log_level is not None else logging.NOTSET )
            sessionHandler.setFormatter( sessionFormatter )
            
            
            if _cfg.status_debug():
                try:
                    statusHandler = logging.FileHandler( os.path.join( logdir , 'status_log' ) , 'a' )
                    statusHandler.setLevel( logging.NOTSET )
                    statusHandler.setFormatter( sessionFormatter )  
                except IOError:
                    statusHandler = logging.FileHandler( '/dev/null' , 'a' )
                    statusHandler.setLevel( logging.ERROR )
            else:     
                statusHandler = logging.FileHandler( '/dev/null' , 'a' )
                statusHandler.setLevel( logging.ERROR )
                
            
            

            #########################
            #                       #
            #        Logger         #
            #                       #
            #########################
            
            root = logging.getLogger()
            root.setLevel( logging.DEBUG )

            mobyle = logging.getLogger('Mobyle')
            mobyle.setLevel( logging.NOTSET )
            mobyle.propagate = False
            mobyle.addHandler( defaultHandler  )
            mobyle.addHandler( mailHandler )
            
            if not child: #can be used Father
                
                cgi = logging.getLogger('mobyle.cgi')
                cgi.propagate = False
                cgi.addHandler( defaultHandler )
                cgi.addHandler( mailHandler )
    
                tc = logging.getLogger('simpleTAL.TemplateCompiler')
                tc.propagate = False
                tc.setLevel( logging.ERROR )
                tc.addHandler( defaultHandler )
                tc.addHandler( mailHandler )
    
                ctc = logging.getLogger('simpleTALES.Context')
                ctc.propagate = False
                ctc.setLevel( logging.ERROR )
                ctc.addHandler( defaultHandler )
                ctc.addHandler( mailHandler )
    
                htc = logging.getLogger('simpleTAL.HTMLTemplateCompiler')
                htc.propagate = False
                htc.setLevel( logging.ERROR )
                htc.addHandler( defaultHandler )
                htc.addHandler( mailHandler )
    
                xtc = logging.getLogger('simpleTAL.XMLTemplateCompiler')
                xtc.propagate = False
                xtc.setLevel( logging.ERROR )
                xtc.addHandler( defaultHandler )
                xtc.addHandler( mailHandler )
                
                parser = logging.getLogger('mobyle.servicestree')
                parser.propagate = False
                parser.addHandler( defaultHandler )
                parser.addHandler( mailHandler )
                
                ##########################################################3
                
                access = logging.getLogger('Mobyle.access')
                access.propagate = False
                access.addHandler( accessHandler )
    
                builder = logging.getLogger('Mobyle.builder')
                builder.propagate = False
                builder.addHandler( builderHandler )
                

                
            else: #can be used in Child
                account = logging.getLogger('Mobyle.account')
                account.propagate = False
                account.addHandler( accountHandler )
                

            #can be used in Father and Child
            session = logging.getLogger('Mobyle.Session')
            session.propagate = False
            #session.setLevel(logging.INFO)
            #session.addHandler( defaultHandler )
            session.addHandler( infoSessionHandler )
            session.addHandler( sessionHandler )
            session.addHandler( mailHandler )
            
            session = logging.getLogger('Mobyle.StatusManager')
            session.propagate = False
            session.addHandler( statusHandler )
            

        return cls._ref
