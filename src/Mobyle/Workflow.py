########################################################################################
#                                                                                      #
#   Author: Herve Menager,                                                             #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################
from lxml import etree #@UnresolvedImport
from Mobyle.Classes.DataType import DataTypeFactory
from Mobyle.Service import MobyleType

parser = etree.XMLParser(remove_blank_text=True)

def xbool(s):
    if s in ['False', 'false', '','0']:
        return False
    else:
        return True

def boolx(s):
    if s==False:
        return 'false'
    else:
        return 'true'

class MobyleElement(etree.ElementBase):

    el_props = {} # properties stored as unique elements
    
    text_props = {} # properties stored as text value of an element
    
    list_props = {} # properties stored as lists of elements

    att_props = {} # properties stored as attributes
        
    PARSER=parser 
    # the parser used will be wired to the MobyleLookup class defined below
    # so that the results of xpath queries are the Mobyle custom classes 
    # instead of generic lxml classes 
    def _init(self):
        self.tag=self.mtag
            
    def __getattr__(self, name):
        if self.text_props.get(name):
            return self._get_text(name)
        elif self.att_props.get(name):
            return self._get_att(name)
        elif self.list_props.get(name):
            return self._get_list(name)
        elif self.el_props.get(name):
            return self._get_el(name)
        else:
            raise AttributeError("Attribute '%s' does not exist in '%s' object" % (name, self.__class__.__name__))
                
    def _get_text(self, name):
        return ''.join(self.xpath(self.text_props[name]+'/text()'))

    def _get_att(self, name):
        r = self.get(self.att_props[name][0])
        if r is not None:
            return self.att_props[name][1](r)

    def _get_list(self, name):
        return self.xpath(self.list_props[name])

    def _get_el(self, name):
        r = self.xpath(self.el_props[name])
        if len(r)==1:
            return r[0]
        else:
            return None

    def __setattr__(self, name, value):
        if self.text_props.get(name):
            self._build_path(self.text_props[name])
            self._set_text(name, value)
            self.xpath(self.text_props[name])[0].text = value
        elif self.att_props.get(name):
            self._set_att(name, value)
        elif self.list_props.get(name):
            self._build_path(self.list_props[name])
            self._set_list(name, value)
        elif self.el_props.get(name):
            self._build_path(self.el_props[name])
            self._set_el(name, value)
        else:
            etree.ElementBase.__setattr__(self, name, value)

    def _build_path(self, path):
        if not(self.xpath(path)):
            p = self
            for tag in path.replace('//','/').split('/'):
                if not(p.xpath(tag)):
                    parser = Parser()
                    p = etree.SubElement(p,tag)
                else:
                    p = p.xpath(tag)[0]

    def _set_text(self, name, value):
        self.xpath(self.text_props[name])[0].text = value

    def _set_att(self, name, value):
        self.set(self.att_props[name][0], self.att_props[name][2](value))        

    def _set_list(self, name, value):
        l = self.xpath(self.list_props[name])
        parser = Parser()
        p = l[0].getparent()
        for i in l:
            p.remove(i)
        for i in list(value):
            p.append(i)

    def _set_el(self, name, value):
        l = self.xpath(self.el_props[name])
        p = l[0].getparent()
        for i in l:
            p.remove(i)        
        p.append(value)

class Workflow(MobyleElement):

    mtag = 'workflow'

    text_props = {
             'name':'head/name',
             'version':'head/version',
             'title':'head/doc/title',
             'description':'head/doc/description',
             'authors':'head/doc/authors'
             }
    
    list_props = {
             'parameters':'parameters//parameter', # WARNING: we do not handle nested paragraph/parameter structures                   
             'tasks':'flow/task',
             'links':'flow/link'                  
             }

    att_props = {
             'id':('id',str,str)
             }

    owner = None # owner name is added to the workflow name in order to get a meaningfull directory in the Mobyle server jobs folder

    def __repr__(self):
        return "workflow[%s] %s" % (self.id, self.name)

    def getName(self): # added for Service class compatibility (called from Job)
        if self.owner is not None: # owner name is added to the workflow name in order to get a meaningfull directory in the Mobyle server jobs folder
            return str(self.owner.getKey()) + "_" + str(self.id) # name= session key + workflow number
        return self.name

    def getUrl(self): # added for Service class compatibility (called from Job)
        if not(self.url):
            return self.name
        else:
            return self.url
        
    def isService(self): # added for Service class compatibility (called from Job)
        return False # cheating Job.py ;)
    
    def getUserInputParameterByArgpos(self): # added for Service class compatibility (called from JobFacade)
        return [p.name for p in self.parameters if not p.isout and not p.isstdout]

    def getParameter(self, name): # added for Service class compatibility (called from JobFacade)
        return [p for p in self.parameters if p.name==name][0]

    def getVdef(self, name): # added for Service class compatibility (called from JobFacade)
        return [p for p in self.parameters if p.name==name][0].vdef

    def getDataType(self,name): # added for Service class compatibility (called from JobFacade)
        df = DataTypeFactory()
        p = [p for p in self.parameters if p.name==name][0]
        datatype_class = p.type.datatype.class_name
        datatype_superclass = p.type.datatype.superclass_name
        if (datatype_superclass in [None,""] ):
            dt = df.newDataType(datatype_class)
        else:
            dt = df.newDataType(datatype_superclass, datatype_class)
        return dt

class Parameter(MobyleElement):

    mtag = 'parameter'

    att_props = {
             'id':('id',str,str),
             'ismaininput':('ismaininput',xbool,boolx),
             'ismandatory':('ismandatory',xbool,boolx),
             'ishidden':('ishidden',xbool,boolx),
             'issimple':('issimple',xbool,boolx),
             'isout':('isout',xbool,boolx),
             'isstdout':('isstdout',xbool,boolx),
             }

    text_props = {
             'name':'name',
             'prompt':'prompt',
             'example':'example'
             }
    
    el_props = {
             'type':'type',
             'vdef':'vdef/value/text()'
            }
    
    def __repr__(self):
        return "parameter[%s] (%s)" % (self.id, self.name)

    def getName(self): # added for Service.Parameter class compatibility (called from JobFacade)
        return self.name

    def promptHas_lang(self, lang): # added for UserValueError class compatibility (called from WorkflowJob)
        return True

    def getPrompt(self, lang):
        return self.prompt

    def isInfile(self): # added for Service.Parameter class compatibility (called from JobFacade)
        mt = self.getType()
        return (not(self.isout) and mt.isFile())
    
    def getDataType( self ) :
        mt = self.getType()
        return mt.getDataType()
        
    def getType(self): # added for Service.Parameter
        try:
            return self._mobyleType
        except AttributeError:
            df = DataTypeFactory()
            datatype_class = self.type.datatype.class_name
            datatype_superclass = self.type.datatype.superclass_name
            if (datatype_superclass in [None,""] ):
                dt = df.newDataType(datatype_class)
            else:
                dt = df.newDataType(datatype_superclass, datatype_class)
            self._mobyleType = MobyleType(dt)
            return self._mobyleType
    

        
class Type(MobyleElement):

    mtag = 'type'

    list_props = {
             'biotypes':'biotype',
             }

    el_props = {
             'datatype':'datatype',
            }

    def __repr__(self):
        return "type %s::%s" % (self.biotypes, self.datatype)


class Biotype(MobyleElement):

    mtag = 'biotype'    

class Datatype(MobyleElement):

    mtag = 'datatype'    

    text_props = {
             'class_name':'class',
             'superclass_name':'superclass'
             }

    def __repr__(self):
        return "datatype %s::%s" % (self.class_name, self.superclass_name)

class Task(MobyleElement):

    mtag = 'task'
    
    att_props = {
             'id':('id',str,str),
             'service':('service',str,str),
             'server':('server',str,str),
             'suspend':('suspend',xbool,boolx)
             }

    list_props = {
             'input_values':'inputValue',
             }

    text_props = {
             'description':'description',
             }

    def __repr__(self):
        return self.id
        #return "task[%s] (%s)" % (self.id, self.service)

class InputValue(MobyleElement):
    
    mtag = 'inputValue'
    
    att_props = {
             'name':('name',str,str),
             'reference':('reference',str,str)
             }

    text_props = {
             'value':'.',
             }

    def __repr__(self):
        return "inputValue[%s]" % (self.name)

class Link(MobyleElement):

    mtag = 'link'
    
    att_props = {
             'id':('id',str,str),
             'from_task':('fromTask',str,str),
             'to_task':('toTask',str,str),
             'from_parameter':('fromParameter',str,str),
             'to_parameter':('toParameter',str,str)
             }

    def __repr__(self):
        return "link[%s] %s:%s->%s:%s" % (self.id, self.from_task, self.from_parameter, self.to_task, self.to_parameter)

import inspect, sys
clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
tagDict = {}
for i in clsmembers:
    if hasattr(i[1],'mtag'):
        tagDict[i[1].mtag] = i[1]

class MobyleLookup(etree.PythonElementClassLookup):

    def lookup(self, document, element):
        name = element.tag
        return tagDict.get(name,None)

parser.set_element_class_lookup(MobyleLookup())

class Parser(object):
    
    def __init__(self):
        self.parser = parser
    
    def parse(self, url):
        """ parse from a URL """
        o = etree.parse(url,self.parser)
        return o.getroot()
    
    def XML(self, str):
        """ parse from a string """
        o = etree.XML(str,self.parser)
        return o
    
    def tostring(self, xml,pretty_print=True):
        return etree.tostring(xml, xml_declaration=True , encoding='UTF-8', pretty_print=pretty_print)