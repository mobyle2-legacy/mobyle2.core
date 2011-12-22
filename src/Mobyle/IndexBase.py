#############################################################
#                                                           #
#   Author: Herve Menager                                   #
#   Organization:'Biological Software and Databases' Group, #
#                Institut Pasteur, Paris.                   #
#   Distributed under GPLv2 Licence. Please refer to the    #
#   COPYING.LIB document.                                   #
#                                                           #
#############################################################
"""
Mobyle.IndexBase
Provides mechanisms to generate, cache, and load Mobyle indexes
"""
import os
from logging import getLogger
i_log = getLogger(__name__)

from Mobyle.ConfigManager import Config
_cfg = Config()

from Mobyle.Registry import registry, ProgramDef, WorkflowDef, ViewerDef
from lxml import etree
import pickle


parser = etree.XMLParser( no_network = False )

class IndexGenerator(object):
    def __init__(self, cls):
        self.indexClass = cls
        
    def load(self, type):
        index_path = os.path.join(_cfg.index_path(), type + self.indexClass.indexFileName)
        try:
            input = open(index_path, 'rb')
            idx = pickle.load(input)
            input.close()
        except IOError:
            idx = {}
            i_log.warning("index file '%s' could not be found, set as empty. Please check documentation: %s." % (index_path,os.path.join(os.environ.get('MOBYLEHOME','$MOBYLEHOME'),'Tools','README')))
        return idx
    
    def dump(self, type, dir, registry=registry):
        output = open(os.path.join(dir, type + self.indexClass.indexFileName), 'wb')
        idx = {}
        for s in getattr( registry, type + 's'):
            try:
                doc = etree.parse(s.path)
                doc.xinclude()
                if (isinstance(s, ProgramDef)):
                    idx[registry.getProgramUrl(s.name, s.server.name)] = self.indexClass.getIndexEntry(doc, s)
                elif (isinstance(s, WorkflowDef)):
                    idx[registry.getWorkflowUrl(s.name, s.server.name)] = self.indexClass.getIndexEntry(doc, s)                    
                elif (isinstance(s, ViewerDef)):
                    idx[registry.getViewerUrl(s.name)] = self.indexClass.getIndexEntry(doc, s)                    
            except:
                i_log.error("Error while generating %s entry for %s/%s" %\
                            (self.indexClass.__name__, s.server.name, \
                             s.name), exc_info=True)
                i_log.error(s.name)
                i_log.error(s.path)
                i_log.error(s.url)

        pickle.dump(idx, output, 2)
        output.close()
        
class Index(object):

    indexFileName=""

    def __init__(self, type):
        ig =IndexGenerator(self.__class__)
        self.index = ig.load(type)
        self.type = type
        
    @classmethod
    def generate(cls, type, dir, registry):
        ig =IndexGenerator(cls)
        ig.dump(type, dir, registry)
        
    @classmethod
    def getIndexEntry(cls, doc):
        raise NotImplementedError
     

def _XPathQuery(node, query, returnType="valueString"):
    """
    _XPathQuery is a helper function to get property values from the XML
    @param node: the node which is queried
    @type node: Element
    @param query: Compiled XPath Query
    @type query: varies
    @param returnType: the type we want returned by the function valueString|valueList|rawResult
    @type string
    """
    try:
        if returnType == "rawResult":
            rawResult = node.xpath(query)
            return rawResult
        else:
            valueList = [n for n in node.xpath(query) \
                         if n and n.strip()!='']
            if returnType == "valueList":
                return valueList
            valueString = ' '.join(valueList)
            if returnType == "valueString":
                return valueString
            raise Exception("unauthorized returnType value (%s), \
                            authorized values are rawResult|valueList|valueString"\
                             % valueString)
    except Exception, e:
        i_log.error(e)
        