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
DataTypeValidator.py

This module is used to validate the datatypes of a Mobyle service description
- The DataTypeValidator class
"""
from lxml import etree
import inspect

from Mobyle.ConfigManager import Config
from Mobyle import Classes
from Local import CustomClasses
_cfg = Config()

from logging import getLogger
v_log = getLogger(__name__)

net_enabled_parser = etree.XMLParser(no_network=False)

class DataTypeValidator(object):
    """
    Check if the Mobyle DataTypes announced by a service are valid, w.r.t:
    * the "Generic" and "Local" Mobyle DataTypes, declared in Python classes
    * the previously seen Mobyle DataTypes (if the validator object is the same,
    it is not a Singleton)
    """

    
    def __init__(self):
        """
        Load the object, which should be reused in successive validations to compare
        the dynamic "XML" DataTypes.
        """
        self.datatypesList = {}
        """
        datatypesList is a dictionary containing the different registered DataTypes in the
        following structure:
        * the key is the DataType name
        * the value is:
          - None if the DataType is "Python-declared"
          - a dictionary if it is declared on the fly, with a 'superclass' key that stores the
            declared superclass, and a list of dictionaries storing the parameter and service 
            where it has been declared.
        """
        self.loadPythonDataTypes()
        
    def loadPythonDataTypes(self):
        """
        load python-defined datatype names
        """
        for name, obj in inspect.getmembers(CustomClasses) + inspect.getmembers(Classes):
            if inspect.isclass(obj) and issubclass(obj,Classes.DataType) and obj!=Classes.DataType:
                self.datatypesList[name.rpartition('DataType')[0]] = None

    def validateDataTypes(self, docPath=None, docString=None):
        """
        validate the datatypes for a service, passed as a path to an XML file or as an XML string.
        @param docPath: the path to the service
        @type docPath: {String}
        @param docString: A string storing the XML corresponding to the service
        @type docString: {String}
        @return: the list of error messages which were generated during validation
        @rtype: {List}
        """
        assert (docPath is not None and docString is None) or (docPath is None and docString is not None), "Please specify either a path or a string. Your parameters:\n-path=%s\n-string=%s" %(docPath, docString)
        if docPath:        
            self.doc = etree.parse(docPath, parser=net_enabled_parser)
        else:
            self.doc = etree.fromstring(docString)
        self.doc.xinclude()
        params = self.doc.xpath('//parameter')
        service_name = self.doc.xpath('/*/head/name/text()')
        errors = []
        for r in params:
            parameter_name = r.xpath('name/text()')[0]
            ctx = "parameter %s: " % parameter_name
            try:
                dt_class = r.xpath('type/datatype/class/text()')[0]
            except IndexError:
                errors.append( ctx + 'the "class" element is empty' )
            dt_sclass = r.xpath('type/datatype/superclass/text()')
            if len(dt_sclass)>0:
                dt_sclass = dt_sclass[0]
            else:
                dt_sclass = None
            if self.datatypesList.has_key(dt_class):
                if self.datatypesList.get(dt_class) is not None and self.datatypesList.has_key(dt_class):
                    if self.datatypesList.get(dt_class).has_key('superclass'):
                        if not(self.datatypesList.get(dt_class).get('superclass')==dt_sclass):
                            where_used_string = ['\n- parameter %s of service %s' % (w['parameter'],w['service']) for w in self.datatypesList.get(dt_class)['where']]
                            errors.append(ctx + "redefining %s which is already defined as a subclass of %s as a subclass of  %s in: " %\
                                (dt_class, self.datatypesList.get(dt_class), dt_sclass, where_used_string))
                        else:
                            self.datatypesList[dt_class]['where'].append({'parameter':parameter_name,'service':service_name})
            else:
                if not(dt_sclass):
                    errors.append(ctx + "unknown datatype %s (no superclass and not defined in Python types)" % dt_class)
                elif not(dt_sclass in self.datatypesList.keys()):
                    errors.append(ctx + "defining the new \"XML\" datatype %s using the unknown %s superclass" % (dt_class, dt_sclass))
                elif not(self.datatypesList.get(dt_class)==None):
                    errors.append(ctx + "defining the new \"XML\" datatype %s using the %s \"XML\" superclass" % (dt_class, dt_sclass))                        
                else:
                    self.datatypesList[dt_class] = {'superclass':dt_sclass,'where':[{'parameter':parameter_name,'service':service_name}]}
        return errors