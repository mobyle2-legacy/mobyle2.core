########################################################################################
#                                                                                      #
#   Author: Herve Menager,                                                             #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################
import urllib #@UnresolvedImport
from logging import getLogger #@UnresolvedImport
log = getLogger(__name__)

from Mobyle.MobyleError import MobyleError


class DataProvider(object):
    """DataProvider is an object that mimicks a session or a job from which a data consumer
    (e.g., another job) gets data files.
    """
    
    @classmethod
    def get(cls, o):
        if hasattr(o,"isLocal") and hasattr(o,"getDir"):
            return o
        elif isinstance(o,basestring):
            return DataProvider(o)
        else:
            raise MobyleError("please provide either a data provider object (Session or Job-like) or a url string")
    
    def __init__(self, url):
        self.url = url
        
    def isLocal(self):
        return not(self.url.startswith('http')) # false but...
    
    def getDir(self):
        return self.url
    
    def getOutputFile(self,fileName): # mimics job's getOutputFile (called by Core toFile() methods)
        return urllib.urlopen('%s/%s' % (self.url, fileName)).read()