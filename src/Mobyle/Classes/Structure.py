########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.        #
#                                                                                      #
########################################################################################

"""
Content the Mobyle Parameter types related to the structural biology
"""
 

from Mobyle.MobyleError import MobyleError , UserValueError , UnDefAttrError
from Mobyle.Classes.Core import *




class StructureDataType(DataType):
    
    @staticmethod
    def convert( value , param ):
        """
        Do the general control and cast the value in the right type.
        if a control or the casting fail a MobyleError is raised.
        
        @param value: the value provide by the User for this parameter
        @type value: String
        @return: 
        """
        raise NotImplementedError ,"ToDo"
    
    @staticmethod
    def validate( param ):
        raise NotImplementedError ,"ToDo"
        

class PropertiesDataType(DataType):
    
    @staticmethod
    def convert( value , param ):
        """
        Do the general control and cast the value in the right type.
        if a control or the casting fail a MobyleError is raised.
        
        @param value: the value provide by the User for this parameter
        @type value: String
        @return: 
        """
        raise NotImplementedError ,"ToDo"
    
    
    @staticmethod    
    def validate( param ):
        raise NotImplementedError ,"ToDo"



    
