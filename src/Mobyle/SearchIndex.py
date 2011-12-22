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
from Mobyle.Registry import *
import re

from logging import getLogger
r_log = getLogger(__name__)

from Mobyle import IndexBase

queries = {
           'head': '/*/head',
           'package': 'package',
           'name': 'name//text()',
           'title': 'doc/title/text()', 
           'description': 'doc/description/text/text()',
           'categories': 'category/text()',
           'comment': 'doc/comment/text/text()',
           'authors': 'doc/authors/text()',
           'references': 'doc/reference/text()',
           'parameter': './/parameter[name]',
           'parameter_name': 'name/text()',
           'parameter_prompt': 'prompt/text()',
           'parameter_comment': 'comment/text/text()',
           'parameter_type': 'type',
           'parameter_biotype': 'biotype/text()',
           'parameter_datatype': 'datatype',
           'parameter_class': 'class/text()',
           'paragraph': '//paragraph',
           'paragraph_name': 'name/text()',
           'paragraph_prompt': 'prompt/text()',
           'paragraph_comment': 'comment/text/text()'
          }

class SearchIndex(IndexBase.Index):

    indexFileName = 'search.dat'

    def filterRegistry(self, keywordList):
        keywordList = [re.escape(k) for k in keywordList] # escape special re characters...
        keywordsRe = re.compile('(%s)' % '|'.join(keywordList), re.I)
        servicesList = getattr( registry, self.type + 's')[:]
        for s in servicesList:
            s.searchMatches = []
            if self.index.has_key(s.url):
                for field, value in self.index[s.url].items():
                    if isinstance(value, basestring):
                        self._searchFieldString(field, value, keywordsRe, s)
                    if isinstance(value, list):
                        for valueItem in value:
                            self._searchFieldString(field, valueItem, keywordsRe, s)
            if len(s.searchMatches) == 0:
                registry.pruneService(s)

    def _searchFieldString(self, fieldName, fieldValue, rx, program):
        if len(rx.findall(fieldValue))>0:
            program.searchMatches.append((fieldName,rx.sub('<b>\\1</b>',fieldValue)))
        
    @classmethod
    def getIndexEntry(cls, doc, index):
        """
        Return an search index entry value
        @return: the index entry: value
        @rtype: object
        """
        head = IndexBase._XPathQuery(doc, queries['head'], 'rawResult')[0]
        fields = {}
        fields['name'] =         IndexBase._XPathQuery(head, queries['name'])
        fields['title'] =        IndexBase._XPathQuery(head, queries['title'])
        fields['description'] =  IndexBase._XPathQuery(head, queries['description'])
        fields['categories'] =   IndexBase._XPathQuery(head, \
                                              queries['categories'], \
                                              'valueList')
        fields['comment'] =      IndexBase._XPathQuery(head, queries['comment'])
        fields['authors'] =      IndexBase._XPathQuery(head, queries['authors'])
        fields['references'] =   IndexBase._XPathQuery(head, queries['references'])
        package = IndexBase._XPathQuery(head, queries['package'], 'rawResult')
        if package:
            package = package[0]
            fields['package name'] =         IndexBase._XPathQuery(package, queries['name'])
            fields['package title'] =        IndexBase._XPathQuery(package, queries['title'])
            fields['package description'] =  IndexBase._XPathQuery(package, queries['description'])
            fields['package categories'] =   IndexBase._XPathQuery(package, \
                                                  queries['categories'], \
                                                  'valueList')
            fields['package comment'] =      IndexBase._XPathQuery(package, queries['comment'])
            fields['package authors'] =      IndexBase._XPathQuery(package, queries['authors'])
            fields['package references'] =   IndexBase._XPathQuery(package, queries['references'])            
        fields['parameter name'] = []
        fields['parameter prompt'] = []
        fields['parameter comment'] = []
        fields['parameter bioTypes'] = []
        fields['parameter class'] = []
        pars = IndexBase._XPathQuery(doc, queries['parameter'], 'rawResult')
        for p in pars:
            fields['parameter name'].append(IndexBase._XPathQuery(p, queries['parameter_name']))
            fields['parameter prompt'].append(IndexBase._XPathQuery(p, queries['parameter_prompt']))
            fields['parameter comment'].append(IndexBase._XPathQuery(p, queries['parameter_comment']))
            parType = IndexBase._XPathQuery(p, \
                                  queries['parameter_type'], 
                                  'rawResult')[0]
            fields['parameter bioTypes'].append(IndexBase._XPathQuery(parType, \
                                         queries['parameter_biotype']))
            parDataType = IndexBase._XPathQuery(parType, \
                                      queries['parameter_datatype'],\
                                      'rawResult')[0]
            fields['parameter class'].append(IndexBase._XPathQuery(parDataType, \
                                      queries['parameter_class']))
        fields['paragraphs'] = []
        pars = IndexBase._XPathQuery(doc, queries['paragraph'], 'rawResult')
        fields['paragraph name'] = []
        fields['paragraph prompt'] = []
        fields['paragraph comment'] = []
        for p in pars:
            fields['paragraph name'].append(IndexBase._XPathQuery(p, queries['paragraph_name']))
            fields['paragraph prompt'].append(IndexBase._XPathQuery(p, queries['paragraph_prompt']))
            fields['paragraph comment'].append(IndexBase._XPathQuery(p, queries['paragraph_comment']))
        return fields
