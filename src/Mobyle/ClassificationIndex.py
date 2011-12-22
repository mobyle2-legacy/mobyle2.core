#############################################################
#                                                           #
#   Author: Herve Menager                                   #
#   Organization:'Biological Software and Databases' Group, #
#                Institut Pasteur, Paris.                   #
#   Distributed under GPLv2 Licence. Please refer to the    #
#   COPYING.LIB document.                                   #
#                                                           #
#############################################################

from Mobyle.Registry import CategoryDef, registry, ServiceTypeDef
from logging import getLogger
r_log = getLogger(__name__)
from Mobyle import IndexBase

queries = {
           # head//category adds the package categories to potential results
           'categories': '/*/head//category',
           'categories_text': 'text()',
           'package': '/*/head/package/name/text()',
           'service_type': 'name(/*)',
          }

class ClassificationIndex(IndexBase.Index):
    
    indexFileName = 'classification.dat'

    def buildRegistryCategories(self, field='category',serviceTypeSort='separate'):
        """
        Builds the categories hierarchy from
        the service definitions, using the categories information
        """
        for s in getattr( registry, self.type + 's'):
            if (not(s.disabled) and (s.authorized) and self.index.has_key(s.url)):
                try:
                    cats = self.index[s.url][field]
                    if len(cats)==0: # display services with no "category" as root
                        if serviceTypeSort=='separate':
                            s.server.addDescendant([ServiceTypeDef(self.index[s.url]['service_type'])]+[s])
                            registry.addDescendant([ServiceTypeDef(self.index[s.url]['service_type'])]+[s])
                        else:
                            s.server.addDescendant([ServiceTypeDef('Services')]+[s])
                            registry.addDescendant([ServiceTypeDef('Services')]+[s])                            
                    for cn in cats:# for each classification of the program
                        lpath = []
                        gpath = []
                        cs = [c for c in cn.split(':') if c!=''] #''=no category (root-level)
                        #per-server classification setup
                        for c in cs:
                            lpath.append(CategoryDef(c))
                        lpath.append(s)
                        #global classification setup
                        for c in cs:
                            gpath.append(CategoryDef(c))
                        if serviceTypeSort=='separate':
                            s.server.addDescendant([ServiceTypeDef(self.index[s.url]['service_type'])]+lpath+[s])
                            registry.addDescendant([ServiceTypeDef(self.index[s.url]['service_type'])]+gpath+[s])
                        else:
                            s.server.addDescendant([ServiceTypeDef('Services')]+lpath+[s])
                            registry.addDescendant([ServiceTypeDef('Services')]+gpath+[s])                            
                except Exception:
                    r_log.error("Error while loading classification for program %s" % s.name, exc_info=True)
                    continue

    @classmethod
    def getIndexEntry(cls, doc, program):
        """
        Return an classification index entry value
        @return: the index entry: value
        @rtype: object
        """
        cats = IndexBase._XPathQuery(doc, queries['categories'], 'rawResult')
        categories=[]
        for cat in cats:
            categories.append(IndexBase._XPathQuery(cat, queries['categories_text'], 'valueString'))
        package = IndexBase._XPathQuery(doc, queries['package'], 'valueList')
        service_type = IndexBase._XPathQuery(doc, queries['service_type'], 'rawResult').capitalize()+'s'
        return {'package':package,'category':categories,'service_type':service_type}