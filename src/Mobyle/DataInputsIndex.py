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
from logging import getLogger
r_log =getLogger(__name__)

from Mobyle import IndexBase

queries = {
           'title': '/*/head/doc/description/text/text()', 
           'name': '/*/head/name/text()', 
           'parameter': './/parameter[name]',
           'parameter_isinput': '(not(@isout) and not(@isstdout) and not(@ishidden))',
           'parameter_name': 'name/text()',
           'parameter_prompt': 'prompt/text()',
           'parameter_type': 'type',
           'parameter_biotype': 'biotype/text()',
           'parameter_datatype': 'datatype',
           'parameter_class': 'class/text()',
           'parameter_superclass': 'superclass/text()',
           'parameter_cardinality': 'card/text()',
           'parameter_dataformats': './/dataFormat/text()',
          }

nifdt = [None, 
         '',
         'Boolean', 
         'Integer', 
         'Float', 
         'String', 
         'Choice', 
         'MultipleChoice', 
         'FileNameDataType', 
         'StructureDataType', 
         'PropertiesDataType']

class DataInputsIndex(IndexBase.Index):
    
    indexFileName = 'inputs.dat'
    
    def getList(self):
        inputs_list = {}
        for key, entry in self.index.items():
            for item in entry:
                inputs_list['%s|%s' % (key, item['name'])] = item
        return inputs_list
    
    @classmethod
    def getIndexEntry(cls, doc, program):
        """
        Return an description index entry value
        @return: the index entry: value
        @rtype: object
        """
        inputParameters=[]
        programName = IndexBase._XPathQuery(doc, queries['name'])
        programPID = programName
        if program.server.name != 'local':
            programName += '@'+program.server.name
            programPID = program.server.name + '.' + programPID
        programTitle = IndexBase._XPathQuery(doc, queries['title'])
        pars = IndexBase._XPathQuery(doc, queries['parameter'], 'rawResult')
        for p in pars:
            parameter = {}
            parameter['isInput'] = str(IndexBase._XPathQuery(p, \
                                            queries['parameter_isinput'],\
                                            'rawResult'))
            parameter['name'] = IndexBase._XPathQuery(p, queries['parameter_name'])
            parameter['programName'] = programName
            parameter['programPID'] = programPID
            parameter['programTitle'] = programTitle
            parameter['prompt'] = IndexBase._XPathQuery(p, queries['parameter_prompt'])
            parType = IndexBase._XPathQuery(p, \
                                  queries['parameter_type'], 
                                  'rawResult')[0]
            parameter['bioTypes'] = IndexBase._XPathQuery(parType, \
                                         queries['parameter_biotype'],"valueList")
            parDataType = IndexBase._XPathQuery(parType, \
                                      queries['parameter_datatype'],\
                                      'rawResult')[0]
            parameter['dataTypeClass'] = IndexBase._XPathQuery(parDataType, \
                                      queries['parameter_class'])
            parameter['dataTypeSuperClass'] = IndexBase._XPathQuery(parDataType, \
                                           queries['parameter_superclass'])
            parameter['dataTypeFormats'] = IndexBase._XPathQuery(parType, \
                                         queries['parameter_dataformats'],"valueList")
            card = IndexBase._XPathQuery(parType, queries['parameter_cardinality'])
            mincard = 1
            maxcard = 1
            if card != '':
                card = card.split(',')
                mincard = card[0]
                if len(card) > 1:
                    maxcard = card[1]
                else:
                    maxcard = card[0]
            parameter['minCard'] = mincard
            parameter['maxCard'] = maxcard
            #parameter['id']=program.url+'|'+parameter['name']
            for key, value in parameter.items():
                if value == '':
                    parameter[key]=None
            if parameter['isInput']=='True' and parameter['dataTypeClass'] not in nifdt:
                inputParameters.append(parameter)
        return inputParameters