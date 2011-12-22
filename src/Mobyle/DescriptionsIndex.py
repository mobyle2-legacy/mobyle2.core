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
Mobyle.Index

This module manages the list of available programs to:
 - search them (using search fields)
 - classify them (building the categories tree)
 - cache this information (on disk as a JSON file)
"""
from Mobyle.Registry import registry

from logging import getLogger
r_log = getLogger(__name__)

from Mobyle import IndexBase

queries = {
           'description': '/*/head/doc/description//text()',
          }

class DescriptionsIndex(IndexBase.Index):
    
    indexFileName = 'descriptions.dat'
    
    def fillRegistry(self):
        for url, description in self.index.items():
            if registry.programsByUrl.has_key(url):
                registry.programsByUrl[url].description = description
            if registry.workflowsByUrl.has_key(url):
                registry.workflowsByUrl[url].description = description
    
    @classmethod
    def getIndexEntry(cls, doc, program):
        """
        Return an description index entry value
        @return: the index entry: value
        @rtype: object
        """
        return IndexBase._XPathQuery(doc, queries['description'])