########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

import imp
from logging import getLogger
e_log = getLogger( __name__ )

from Mobyle.MobyleError import MobyleError , EvaluationError


__extra_epydoc_fields__ = [('call', 'Called by','Called by')]




class Evaluation:
    """
    The Evaluation Class stock the parameter values and permit to evaluate expression (Ctrl precond format ...) in a protected environment avoidig names collision
    """
    def __init__(self):
        try:
            fp , pathname , description = imp.find_module("re")
            self.re = imp.load_module( "re" , fp , pathname , description )
            
        finally:
            if fp:
                fp.close()

        
    def isFill( self ):
        """
        @return: returns True if the Evaluation is already filled, if there isn't any user value in evalution return False.
        @rtype: boolean
        """
        
        for var in self.__dict__.keys():
            if var == "re" or var == "__builtins__":
                continue
            else:
                return True
        return False


    def _2dict_( self ):
        """
        @return: Returns a dictionary containing the attributes creates by L{setVar}
        @rtype: dictionary
        """
        dict = {}
        
        for param in self.__dict__.keys():
            if param == "__builtins__" or param == "vdef" or param == "value" or param == "re" :
                pass
            else:
                dict[ param ] = self.__dict__[ param ]
                
        return dict

    def setVar(self, varName , value):
        """
        Creates an attribute varName with the value value
             
        @param varName: the name of the attribute to create
        @type varName: String
        @param value: the value of the attribute varName
        @type value: any
      
        """
        setattr(self , varName , value)
  

    def getVar(self, varName):
        """
        @param varName: the name of the parameter 
        @type varName: String
        @return: the value of the varName attribute or None if there is no attribute varName  
        """
        try:
            return getattr(self, varName)
        except AttributeError:
            return None
   
          
    def eval(self, expr):
        """
        eval the expr in self namespace. be careful to specify the value and vdef before calling eval.
        @param expr: the expression to evalute
        @type expr: String
        @return: the expression evaluated in the Evalution namespace
        @todo: evaluer le temps passe a importe re a chaque fois, le faire que si re dans la string a evalue?
        """
        try:
            myEval = eval( expr , vars(self) )
            return myEval
        
        except Exception , err:
            raise EvaluationError , err
                  


    def isDefined(self, varName):
        """
        we decided to fill the evaluation instance with all the parameter of the service.
        if the user provide a value or there is a vdef for the parameter the value is affected
        to the parameter.
        else the parameter will be affected at None
        @return: True if the varName has been defined (not None), False Otherwise
        """
        try:
            if getattr(self, varName) == None:
                return False
            else:
                return True
        except NameError:
            msg = "the variable: "+str(varName)+" is unknown"
            e_log.error(msg)
            raise MobyleError , msg

                  

