########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.        #
#                                                                                      #
########################################################################################

from exceptions import Exception

class MobyleError(Exception):

    def __init__(self, msg = None):
        self._message = str( msg )
    
    def _get_message(self):
        return self._message
    #workaround to ensure Mobyle compatibility
    #with either python 2.5 and python 2.6
    #as self.message is deprecated in python 2.6
    message = property( fget = _get_message )
    
    def _get_param(self):
        return self._param
    param = property( fget = _get_param )
    
    def __str__(self, *args, **kwargs):
        return self.message

class ServiceError(MobyleError):
    pass

class ParameterError(ServiceError):
    pass

class ConfigError(MobyleError):
    pass

class ParserError( MobyleError ):
    pass

class UnDefAttrError(ParameterError):
    """
    Raised  when attempt to apply a method on a parameter attribute which is not exist  
    """
    pass
 
class UserValueError(MobyleError):
    """
    Raised when the user do a mistake. ex a wrong value for a parameter or forget to specify a mandatory parameter...
    """
    def __init__(self, parameter = None , msg = None):
        self._param = parameter
        self._message = msg
    
    def __str__(self):
        
        #lang = Mobyle.ConfigManager.Config().lang()
        #problem d'import cyclique
        # TOFIX
        lang = 'en'
        
        if self._param:
            if self._param.promptHas_lang( lang ):
                try:
                    err_msg = self._param.getPrompt( lang ) + " = " + self._message
                except:
                    err_msg = "%s : invalid value" % self._param.getPrompt( lang )
            else:
                if self._param.promptLangs():
                    try:
                        err_msg =self._param.getPrompt( self._param.promptLangs()[0] ) + " = " + self._message
                    except:
                        err_msg = "%s : invalid value" % self._param.getPrompt( self._param.promptLangs()[0] )
                else:
                    try:
                        err_msg = self._param.getName() + self._message
                    except:
                        err_msg = "%s : invalid value" %self._param.getName() 
        else:
            err_msg = self._message
        return err_msg


class UnSupportedFormatError( MobyleError ):
    pass

class EvaluationError( MobyleError ):
    pass

class NetError( MobyleError ):
    pass

class HTTPError( NetError ):
    def __init__(self, *args):
        self.code = args[0].getCode()

class URLError( NetError ):
    pass

class JobError( MobyleError ):
    def __init__(self, *args):
        self.errno = args[0]
        self.strerror = args[1]
        self.jobID = args[2]
        
    def __str__(self):
        return "[ Errno %d] Cannot open Job %s : %s "%( self.errno , 
                                                        self.jobID ,
                                                        self.strerror ,
                                                        )
class SessionError( MobyleError ):
    pass

class EmailError( MobyleError ):
    pass

class TooBigError( EmailError ):
    pass

class AuthenticationError( SessionError ):
    pass
    
class NoSpaceLeftError( SessionError ):
    pass