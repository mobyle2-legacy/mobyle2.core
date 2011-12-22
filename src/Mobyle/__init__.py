########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.        #
#                                                                                      #
########################################################################################

__all__ = [

]

"""
            'CommandBuilder',
           'Evaluation',
           'Job' ,
           'MobyleError' ,
           'MobyleJob' ,
           'ConfigManager',
           'Parser' ,
           'Service',
           'Session',
           'AuthenticatedSession',
           'AnnonymousSession',
           'Transaction',
           'RunnerFather',
           'RunnerChild',
           'JobState',
           'Classes',
           'SequenceConverter' ,
           'AlignmentConverter' ,
           'Utils',
           'Net',
           'Execution' ,
           'Converter' ,
           'JobFacade' ,
           'Workflowjob',
"""
# See http://peak.telecommunity.com/DevCenter/setuptools#namespace-packages
try:
    __import__('pkg_resources').declare_namespace(__name__)
except ImportError:
    from pkgutil import extend_path
    __path__ = extend_path(__path__, __name__)
