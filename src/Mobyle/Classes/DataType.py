########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

"""

"""

import os , os.path , re
import types
from logging import getLogger
c_log = getLogger(__name__)

from Mobyle.MobyleError import MobyleError


class DataType( object ):

    def __init__( self , name = None ):
        if name:
            self.name = name
        else:
            self.name = self.__class__.__name__[0:-8]
        
        self.ancestors = [ k.__name__[0:-8] for k in self.__class__.mro() ][0:-2]

        if self.name not in self.ancestors :
            self.ancestors.insert( 0 , self.name )
        
            
    def isPipableToDataType( self , targetDataType ):
        return targetDataType.name in self.ancestors

    def getName( self ):
        return self.name
    
    def isFile( self ):
        return False
    
    def toDom( self ):
        """
        @return: a dom representation of this datatype
        @rtype: element
        """
        from lxml import etree        
        
        if self.name == self.__class__.__name__[0:-8] :
            klass = self.name
            superKlass = None 
        else:
            klass = self.name
            superKlass = self.__class__.__name__[0:-8]
            
        dataTypeNode = etree.Element( "datatype" )
        klassNode = etree.Element( "class" )
        klassNode.text =  klass 
        dataTypeNode.append( klassNode )
        if superKlass :
            superKlassNode = etree.Element( "superclass" )
            superKlassNode.text =  superKlass 
            dataTypeNode.append( superKlassNode )
        return dataTypeNode 

    def __eq__(self , other ):
        return self.ancestors == other.ancestors
    
    def __str__(self):
        return self.name
    
        
class DataTypeFactory( object ):
    
    _ref = None
    
    def __new__( cls ):
        if cls._ref is None:
            cls._ref = super( DataTypeFactory , cls ).__new__( cls )
        return cls._ref
    
    def __init__(self):
        self.definedDataTypes = {}
        
    def newDataType( self , name , xmlName = None ):
        """
        @param name: the value of element superclass or class if there is no superclass
        @type name: string
        @param xmlName: the value of element class when the element superclass is specify
        @type xmlName: string
        @return: an instance of datatype according to the name and xmlName
        @rtype: a Datatype instance   
        """
        if xmlName:
            realName = xmlName + "DataType"
        else:
            try:
                realName = name + "DataType"
            except TypeError:
                raise MobyleError , "the argument \"name\" must be a string ( %s received )" %str( type( name )) 
        if self.definedDataTypes.has_key( realName ):
            dt = self.definedDataTypes[ realName ]
            
            if( dt.__class__.__name__[0:-8] != name ):
                c_log.error("consistency error:")
                raise MobyleError , "consistency error: a \"%s\" is already defined with python type \"%s\" instead of \"%s\"" %( dt.getName() ,
                                                                                                                                 dt.__class__.__name__[0:-8] ,
                                                                                                                                 name 
                                                                                                                                 )
            
            return dt
        
        else:
            if not xmlName :
                dts = name + 'DataType()'
            else:
                dts = name + 'DataType( name = "' + str( xmlName ) + '")'
            
            #the import is not at top level to avoid cyclic import
            #between DataType , Core.py , Sequence.py , Structure.py and Local.CustomClasses
            import  Mobyle.Classes
            fulldts = "Mobyle.Classes." + dts
            try:
                self.definedDataTypes[ realName ] = eval( fulldts )
            except ( NameError, AttributeError ) , err:
                import  Local.CustomClasses
                fulldts = "Local.CustomClasses." + dts
                try:
                    self.definedDataTypes[ realName ] = eval( fulldts )
                except ( NameError, AttributeError ) , err:
                    msg = "can't find DataType : \"%s\" in Mobyle" %( dts )
                    c_log.error(msg)
                    raise MobyleError , msg
                except:
                    raise MobyleError , "invalid CustomDataType : %s" %( dts )
            except:
                raise MobyleError , "invalid DataType : %s" %( dts )
            return self.definedDataTypes[ realName ]



    def issubclass(self , dataType1 , name2 , xmlName2= None ):
        """
        @param dataType1: the dataType to test
        @type dataType1: instance of a Datatype
        @param name2: the value of element superclass or class if there is no superclass
        @type name2:  string
        @param xmlName2: the value of element class when the element superclass is specify
        @type xmlName2:  string
        @return: True if dataType1 is an instance of the datatype represente by name2 , xmlName2. False otherwise  
        @rtype: boolean
        """
        dataType2 = self.newDataType( name2 , xmlName= xmlName2 )
        try:
            return  issubclass( dataType1.__class__ , dataType2 .__class__ )
        except AttributeError , err :
            raise TypeError , "there is no DataType named "+ str( name2 )
    


