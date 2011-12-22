########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

from logging import getLogger
b_log = getLogger('Mobyle.builder')
s_log = getLogger( __name__ )

import types
import os

from Mobyle.MobyleError import MobyleError , ServiceError , UnDefAttrError , ParameterError , UserValueError
from Mobyle.Evaluation  import Evaluation
from Mobyle.ConfigManager  import Config
_cfg = Config()
__extra_epydoc_fields__ = [('call', 'Called by','Called by')]




###############################################################
#                                                             #
#                      Class Program                          #
#                                                             #
###############################################################


class Program(object):
    """
    a Program object is the Python representation of the xml program definition
    and had methods to manage the data
    """
    _paramError = " this program doesn't content parameter named : "
    
    def __init__(self, evaluator = None , ):
        """
        this object is the python representation of program describe in xml
        @call: indirectly in L{MobyleJob._makeProgram}
        @call: indirectly in L{RunnerChild} main
        """
        self._debug = None #set to cfg.debug( ProgramName ) by setName()
        
        if evaluator is None:
            self._evaluator = Evaluation()
        else:
            self._evaluator = evaluator
            
        self.cfg = Config()
        self.header = Header()
        self._parameters = Parameters()
        
    def _getAllParameter(self):
        """
        @return: all  L{Parameter}'s instance in a list
        @rtype: list of Parameter
        @call: L{getAllParameterNameByArgpos}
        @call: L{getCommandParameterName}
        """
        return self._parameters.getAllParameter()

    def getAllParameterByArgpos(self):
        """
        @return: a list of all  L{parameter's <Parameter>}  sorted by their argpos.
        @rtype: list of L{parameter's <Parameter>}
        """
        paramList = self._getAllParameter()
        paramList.sort(self.cmpPara)
        return paramList
            
    def getAllParameterNameByArgpos(self):
        """
        @return: a list of all  L{parameter's <Parameter>} name sorted by their argpos.
        @rtype: list of string
        @call: L{CGIJob.form2Dict} L{MobyleJob.__init__} L{MobyleJob._fillEvaluator} L{MobyleJob._validateParameters}
        @call: L{getAllHiddenParameter}, L{getAllSimpleParameter}, L{getAllMandatoryParameter}
        """
        paramList = self._getAllParameter()
        paramList.sort(self.cmpPara)
        return [ p.getName() for p in paramList ] 

    def getUserInputParameterByArgpos( self ):
        paramList = self._getAllParameter()
        paramList.sort( self.cmpPara )
        result = []
        for param in paramList:
            if not param.isout() and not param.ishidden():
                result.append( param.getName() )
        return result


    def getAllParagraphNameByArgpos(self):
        """
        @return: a list of all  L{Paragraph}'s name sorted by their argpos.
        @rtype: list of string
        """
        paragList = self._getAllParagraph()
        paragList.sort(self.cmpPara)
        result = []
        for parag in paragList:
            result.append( parag.getName() )
        return result

    def cmpPara(self ,para1 , para2 ):
        """
        compare two  L{parameter <Parameter>} or  L{paragraph <Paragraph>} according to their argpos.
        @rtype: int  
        @return:
          - negative number if para1 > para2
          - 0 if para1 and para2 are equal
          - positive number otherwise
        @call: L{getAllParameterNameByArgpos}, L{getAllParagraphNameByOrder}
        """ 
        argpos1 = para1.getArgpos()
        argpos2 = para2.getArgpos()    
        return argpos1 - argpos2

    def getDebug(self):
        return self.cfg.debug( self.header.getName() )
    
    def getAllHiddenParameter(self):
        """
        @return: a list of all hidden parameter's name sorted by their argpos.
        @rtype: list of strings.
        """
        result = []
        for paramName in self.getAllParameterNameByArgpos():
            if self.ishidden(paramName):
                result.append( paramName )
        return result
    

    def getAllSimpleParameter(self):
        """
        @return: A list of all simple parameter's name sorted by their argpos.
        @rtype: list of strings.
        """
        result = []
        for paramName in self.getAllParameterNameByArgpos():
            if self.issimple(paramName):
                result.append( paramName )
        return result


    def getAllMandatoryParameter(self):
        """
        @return: A list of all mandatory parameter's name sorted by their argpos.
        @rtype: list of strings.
        """
        result = []
        for paramName in self.getAllParameterNameByArgpos():
            if self.ismandatory(paramName):
                result.append( paramName )
        return result


    def getAllOutParameter(self):
        """
        @return: A list of all out parameter's name sorted by their argpos.
        @rtype: list of strings.
        """
        result = []
        for paramName in self.getAllParameterNameByArgpos():
            if self.isout( paramName ) or self.isstdout( paramName ):
                result.append( paramName )
        return result

   
    def getAllOutFileParameter(self):
        """
        @return: A list of all out parameter
        @rtype: list of Parameter instances.
        """
        result = []
        for param in self._getAllParameter():
            if param.isOutfile() :
                result.append( param )
        return result

    def getAllInFileParameter(self):
        """
        @return: A list of all in parameter.
        @rtype: list of Parameter instances.
        """
        result = []
        for param in self._getAllParameter():
            if param.isInfile() :
                result.append( param )
        return result

        
    def getCommandParameterName(self):
        """
        @return: The name of the first parameter with attribute iscommand= True.
         ( it should be have only one parameter with iscommand = True per Program).
          If doesn't find any parameter with iscommand = True, return None.
        @rtype: a not empty string or None.
        @call:  L{CommandBuilder.buildLocalCommand<CommandBuilder>}
        """
        for param in self._getAllParameter():
            if param.iscommand():
                return param.getName()
        return None

    def addheader(self , header ):
        CommandParameterName = self.getCommandParameterName()
        if CommandParameterName :
            msg = "try to add a header with a command but \"%s\" parameter is already used as command" % CommandParameterName
            s_log.error( msg )
            raise ServiceError , msg
        self.header = header
        self.debug = self.cfg.debug( header.getName() ) 
    
    def addParameter(self, parameter):
        """
        Add a  L{parameter <Parameter>} instance or a sequence of L{parameter <Parameter>} instances at the Program top level.
        @param parameter: the parameter to add
        @type parameter: a -L{Parameter} instance
        """
        if type(parameter) == type([]) or type(parameter) == type( () ):
            for param in parameter:
                self._parameters.addParameter(param)
                param.setFather(self)
                param.setEvaluator(self._evaluator)
        else:
            self._parameters.addParameter(parameter)
            parameter.setFather(self)
            parameter.setEvaluator(self._evaluator)
            
    def getParameter(self, paramName):
        """
        @return: the  L{Parameter} instance which have the name paramName. if no parmeter found return None
        @rtype: a  L{Parameter} instance or None
        @call: by all Sevice methods which are delegated to parameter
        """
        return self._parameters.getParameter( paramName )
       
    def _getAllParagraph(self):
        """
        @return: all  L{Paragraph} instances from all levels
        @rtype: a list of  L{Paragraph} instances
        @call: L{getAllParagraphNameByOrder}
        """
        return self._parameters.getAllParagraph()


    def _getParagraph(self, paragName):
        """
        @param paragName: the name of the paragraph
        @type paragName: String
        @return: the  L{Paragraph} instance which have the name paragName. If no pragraph with name paragName was found, return None.
        @rtype: a   L{Paragraph} instance
        @call: L{getInfo}
        """
        return self._parameters.getParagraph( paragName)


    def addParagraph(self, paragraph):
        """
        Add a  L{Paragraph} or a sequence of Paragraph instance at the Program top level
        @param paragraph: the paragraph to add
        @type paragraph:  L{Paragraph} instance.
        """
        if type(paragraph) == type([]) or type(paragraph) == type( () ):
            for parag in paragraph:
                self._parameters.addParagraph(parag)
                parag.setFather(self)
                parag.setEvaluator(self._evaluator)
        else:
            self._parameters.addParagraph(paragraph)
            paragraph.setFather(self)
            paragraph.setEvaluator( self._evaluator)


    def getPath(self, name):
        """
        @param name: a name of the  L{Paragraph} or  L{Parameter}
        @type name: String
        @return: a string corresponding to the path of the paragraph or parameter name. each name is separated by a /
        @rtype: string
        @call: L{Parameters.getPath} , L{Program.getPath}
        """
        return self._parameters.getPath(self, name)

    def _getPara(self, name):
        """
        @param name: the name of a Parameter or a Paragraph
        @type name: String
        @return: an instance of the  L{Parameter} or the  L{Paragraph} which have the name name. this  method is used by methods which could call either with a parameter or a paragraph as argument eg get/setArgpos()
        @rtype: an object of L{Para} type. Para is an abstract class thus in fact a  L{Parameter} or the  L{Paragraph} instance.
        @call: by all Program methods delegated to the Para L{Para.getPrompt} , L{Para.promptLangs}, L{Para.promptHas_lang}, L{Para.setPrompt}, L{Para.hasFormat}, L{Para.getFormat}, L{Para.formatHas_proglang}, L{Para.formatProglangs}, L{Para.setFormat}, L{Para.getPrecond}, L{Para.precondHas_proglang}, L{Para.precondProglangs}. 
        """
        result = self.getParameter(name)
        if result :
            return result
        else:
            return self._getParagraph(name)

        
    def addInfo(self, content, proglang = None , lang = None , href = False):
        """
        Set an info on this Program
        Only one of the arguments proglang, lang or href must be specified. If more than one arguments among these are specified, a  L{ServiceError} is raised.
        @param content: an info on the Program or a href toward an info
        @type content: String
        @param proglang: the programming language of the info code
        @type proglang: String
        @param lang: is the symbol of a language in  iso639-1 (ex:english= 'en',french= 'fr') 
        @type lang: String
        @param href: True if the content is a href, False otherwise
        @type href: Boolean
        """
        if ( (proglang and lang) or (proglang and href) or (lang and href) ):
            raise ServiceError, "an info couldn't be a text and a code or href in the same time"
        if proglang:
            self._parameters.addInfo( content , proglang = proglang)
        elif lang:
            self._parameters.addInfo( content , lang = lang)
        elif href:
            self._parameters.addInfo( content )
        else :
            raise ServiceError, "invalid argument for info : " + str(proglang) + str(lang) + str(href)
        
        

    def getInfo(self, paragraphName=None, proglang =None ,lang= None, href = False):
        """
        Only one of the arguments proglang, lang or href must be specified. If more than one arguments among these are specified, a  L{ServiceError} is raised.
        @param paragraphName: the name of a paragraph, if paragraphName = None the method return the info of the Program. if paragraphName couldn't be found a ServiceError will be raised
        @type paragraphName: String
        @param proglang: The programming language of the info code
        @type proglang: String
        @param lang: is the symbol of a language in iso639-1 (ex: 'en', 'fr') for a text info
        @type lang: String
        @param href: True if the info is a href, False otherwise
        @type href: Boolean
        @return: the info corresponding to the specified lang, proglang or href.
        @rtype: string.
        """
        if ( (proglang and lang) or (proglang and href) or (lang and href) ):
            raise ServiceError, "an info couldn't be a text and a code or a href in the same time "
        if paragraphName:
            paragraph = self._getParagraph(paragraphName)
            if paragraph:
                if proglang:
                    return paragraph.getInfo( proglang = proglang)
                elif lang:
                    return paragraph.getInfo( lang = lang)
                elif href:
                    return paragraph.getInfo( )
                else :
                    raise ServiceError, "invalid argument for info : " +str(lang)+" , "+str(proglang)+" , "+str(href)
            else:
                raise ServiceError, "the paragraph with name "+str(paragraphName)+" doesn't exist"
        else:
            if proglang:
                return self._parameters.getInfo( proglang = proglang)
            elif lang:
                return self._parameters.getInfo( lang = lang)
            elif href:
                return self._parameters.getInfo( )
            else :
                raise ServiceError, "invalid argument for info : " +str(lang)+" , "+str(proglang)+" , "+str(href)

               
    def infoProglangs(self):
        """
        @return: the list of programming languages used by the info codes.
        @rtype: list of string.
        """
        return self._parameters.infoProglangs()

    def infoHas_lang(self, lang='en'):
        """
        @param lang: the symbol of a language in iso639-1 (ex: 'en', 'fr') 
        @type lang: String
        @return: True if the info has a text written in lang. False otherwise.
        @rtype: boolean.
        """
        return self._parameters.infoHas_lang( lang= lang)
        

    def infoLangs(self):
        """
        @return: the list of languages used by the info texts
        @rtype: a list of string.
        """
        return self._parameters.infoLangs()
         

    def infoHas_href(self):
        """
        @return: True if the info has a 'href', False otherwise.
        @rtype: boolean.
        """
        return self._parameters.infoHas_href() 
        
    ##############################################
    #                                            #
    #     delegated methods to the header        #
    #                                            #
    ##############################################
    def getTitle(self):
        """
        @return: a String representing the  L{Program} title
        @rtype: string
        """ 
        return self.header.getTitle()
    

    def getUrl(self):
        """
        @return: the url of the definition of this Program
        @rtype: string
        """
        return self.header.getUrl()
    

    def getName(self):
        """
        @return: a String resprenting the name of the L{Program}.
        @rtype: string
        """
        return self.header.getName()
        
      
    def getVersion(self):
        """
        @return: a String representing the version of the program
        @rtype: string
        """
        return self.header.getVersion()


    def getDoclinks(self):
        """
        @return: a list of Strings. Each String represent a documentation link
        """
        return self.header.getDoclinks()


    def getHelp(self, lang = None, proglang =None , href = False):
        """
        Only one of the arguments proglang, lang or href must be specified. If more than one arguments among these are specified, a  L{ServiceError} is raised.
        @param proglang: The programming language of the help code
        @type proglang: String
        @param lang: is the symbol of a lang in iso639-1 (ex: 'en', 'fr') for the text 
        @type lang: String
        @param href: True if the content is a href false otherwise
        @type href: boolean
        @return: the help corresponding to the specified lang or proglang or href
        @rtype: string.
        """
        self.header.getHelp(lang = lang, proglang =proglang , href = href )

               
    def helpHas_proglang(self, proglang = 'python'):
        """
        @param proglang: the programming language that encode the help
        @type proglang: String
        @return: True if a code written in proglang is used for the help,
        False otherwise.
        @rtype: boolean.
        """
        return self.header.helpHas_proglang( proglang = proglang)

    def helpProglangs(self):
        """
        @return: the list of proglangs used for the code help.
        @rtype: list of string.
        """
        return self.header.helpProglangs()

    def helpHas_lang(self, lang='en'):
        """
        @return: True if the help has a text written in lang. False otherwise
        @rtype: boolean.
        """
        return self.header.helpHas_lang( lang= lang)
        

    def helpLangs(self):
        """
        @return: the list of langs used for the help texts.
        @rtype: a list of string
        """
        return self.header.helpLangs()
         

    def helpHas_href(self):
        """
        @return: True if the help has a 'href', False otherwise.
        @rtype: boolean
        """
        return self.header.helpHas_href()

        
    def helpHrefs(self):
        """
        @return: The list of href for the help.
        @rtype: list of string 
        """
        return self.header.helpHrefs()

        
    def getCommand(self):
        """
        @return: (name, type , path)
          1. for local program:
              - name is the name of the program
              - type is 'local' (by default)
              - path is the path where is the program (by default the $PATH variable) 
          2. for cgi:
              - name is the name of the cgi
              - type is the method to call the cgi ( GET | POST | POSTM )
              - path is the url where is the script 'http://www.myDomain.org'
          3. for web Program:
              - name is the name of the method
              - type is the protocol to call the ws (soap | xml-rpc | ... )
              - path is the url of the wsdl
        @rtype: tuple of 3 string (name, type, path).
        @call: L{CommandBuilder.BuildLocalCommand<CommandBuilder>}
        """
        return self.header.getCommand()

    def getEnv(self, varName):
        """
        @param varName: the name of the environment variable.
        @type varName: String
        @return: the value of the environment variable,  if there is no environment variable return None.
        @rtype: string or None
        @call: L{CommandBuilder.BuildLocalCommand<CommandBuilder>}
        """
        return self.header.getEnv(varName ) 


    def envHas_var(self, var):
        """
        @param var: the name of the environment variable
        @type var: String
        @return: True the variable var is specified, False otherwise.
        @rtype: boolean.
        """
        return self.header.envHas_var(var)
    
    def envVars(self):
        """
        @return: the names of all environment variables.
        @rtype: string
        @call: L{CommandBuilder.BuildLocalCommand<CommandBuilder>}
        """
        return self.header.envVars()
    
            
    def getCategories(self):
        """
        @return: the list of String, each string representing
        a category in which the Program is classified.
        @rtype: a list of String
        """
        return self.header.getCategories()


    ##############################################
    #                                            #
    #     delegated methods to the parameter     #
    #                                            #
    ##############################################

    
    def setValue(self, paramName, value):
        """
        Set the current value for this parameter.        
        @param paramName: a parameter name
        @type paramName: String
        @param value: the value to set for this parameter
        @type value: any
        @raise  ServiceError: If the paramName doesn't match with any parameter name a  L{ServiceError} is raised.
        @call: L{MobyleJob}._fillEvaluator()
        """
        param = self.getParameter( paramName )
        if param :
            param.setValue( value )
        else:
            raise ServiceError ,self._paramError + str( paramName )

        
    def getValue(self, paramName):
        """
        @param paramName: a parameter name
        @type paramName: String
        @return: The current value of the parameter. if the value is not defined return None
        @raise ServiceError: If the paramName doesn't match with any parameter name a  L{ServiceError} is raised.
        @call: L{CommandBuilder.BuildLocalCommand<CommandBuilder>}, L{doCtrls}
        """
        param = self.getParameter( paramName)
        if param :
            return param.getValue()
        else:
            raise ServiceError , self._paramError + str( paramName )

    def setValueAsVdef( self , paramName ):
        """
        @param paramName: a parameter name
        @type paramName: String
        @raise ServiceError: If the paramName doesn't match with any parameter name a  L{ServiceError} is raised.
        @call: 
        """
        param = self.getParameter( paramName )
        if param :
            param.setValueAsVdef()
        else:
            raise ServiceError ,self._paramError + str( paramName )

    def reset( self , paramName ):
        """
        @param paramName: a parameter name
        @type paramName: String
        @raise ServiceError: If the paramName doesn't match with any parameter name a  L{ServiceError} is raised.
        @call: 
        """
        param = self.getParameter( paramName )
        if param :
            return param.reset()
        else:
            raise ServiceError ,self._paramError + str( paramName )

    def resetAllParam( self ):
        """
        @param paramName: a parameter name
        @type paramName: String
        @raise ServiceError: If the paramName doesn't match with any parameter name a  L{ServiceError} is raised.
        @call: 
        """
        params ={}
        for param in self._getAllParameter():
            params[ param.getName() ] = param.reset()
        return params


    def validate(self, paramName):
        """
        @param paramName: a parameter name
        @type paramName: String
        @return: True if the value is valid. otherwise a UserValueError is raised.
        @raise ServiceError: If the paramName doesn't match with any parameter name a  L{ServiceError} is raised.
        @raise UserValueError: a  L{UserValueError} is raised if the value can't be validate.
        @call: L{MobyleJob}
        """
        param = self.getParameter( paramName)
        if param :
            param.validate()
        else:
            raise ServiceError , self._paramError + str( paramName )

    def convert(self, paramName , value , acceptedMobyleType ):
        """
        @param paramName: a parameter name
        @type paramName: String
        @param value: the value to convert
        @type value: any
        @return: the value cast in the right type
        @raise ServiceError: If the paramName doesn't match with any parameter name a  L{ServiceError} is raised.
        @raise :
        @call: L{MobyleJob , CommnadBuilder}
        """
        param = self.getParameter( paramName)
        if param :
            return param.convert( value , acceptedMobyleType )
        else:
            raise ServiceError , self._paramError + str( paramName )

        
    def getType(self , paramName ):
        """
        @param paramName: a parameter name
        @type paramName: String
        @return: a mobyle Type of this parameter.
        @rtype: L{MobyleType} instance
        @raise ServiceError: If the paramName doesn't match with any parameter name a  L{ServiceError} is raised.  
        """        
        param = self.getParameter( paramName)
        if param :
            return param.getType()
        else:
            raise ServiceError , self._paramError + str( paramName )
 
    
    def getDataType(self , paramName ):
        """
        @param paramName: a parameter name
        @type paramName: String
        @return: the data type of this parameter.
        @rtype: ( string class , string superclass | None )
        @raise ServiceError: If the paramName doesn't match with any parameter name a  L{ServiceError} is raised.  
        """        
        param = self.getParameter( paramName)
        if param :
            return param.getDataType()
        else:
            raise ServiceError , self._paramError + str( paramName )
    
    def getBioTypes( self , paramName):
        param = self.getParameter( paramName)
        if param :
            return param.getBioTypes()
        else:
            raise ServiceError , self._paramError + str( paramName )
  
    def getAcceptedDataFormats( self , paramName):
        param = self.getParameter( paramName)
        if param :
            return param.getAcceptedDataFormats()
        else:
            raise ServiceError , self._paramError + str( paramName )
    
    def forceReformating( self ,  paramName):
        param = self.getParameter( paramName)
        if param :
            return param.forceReformating()
        else:
            raise ServiceError , self._paramError + str( paramName )
    
    def getDataFormat( self , paramName):
        param = self.getParameter( paramName)
        if param :
            return param.getDataFormat()
        else:
            raise ServiceError , self._paramError + str( paramName )

    def hasVdef(self,paramName):
        """
        @param paramName: a parameter name
        @type paramName: String
        @return: True if the parameter has a defined vdef, False otherwise.
        @rtype: boolean.
        @raise ServiceError: If the paramName doesn't match with any parameter name a  L{ServiceError} is raised.
        """
        param = self.getParameter( paramName)
        if param :
            if param.vdefKeys():
                return True
            else:
                return False
        else:
            raise ServiceError , self._paramError + str( paramName )
        
    def getVdef( self , paramName ):
        """
        If the paramName doesn't match with any parameter name a  L{ServiceError} is raised.
        @param paramName: a parameter name
        @type paramName: String
        @return: the default value for the parameter.it could be a code or a list of value
        @rtype: String or list (it's depends of the parameter type).
        @raise ServiceError: If the paramName doesn't match with any parameter name a  L{ServiceError} is raised.
        """
        param = self.getParameter( paramName)
        if param :
            return param.getVdef()
        else:
            raise ServiceError , self._paramError + str( paramName )


    def ismandatory(self, paramName ):
        """
        @param paramName: a parameter name
        @type paramName: String
        @return: True if this parameter must be specify by the user, False otherwise.
        @rtype: boolean
        @raise ServiceError: If the paramName doesn't match with any parameter name a  L{ServiceError} is raised.
        @call: by  L{Job.__init__()}
        """
        param = self.getParameter( paramName )
        if param :
            return param.ismandatory()
        else:
            raise ServiceError , self._paramError + str( paramName )
                                                                      

    def ishidden(self ,paramName):
        """
        @param paramName: a parameter name
        @type paramName: String
        @return: True if this parameter is hidden in html interface, False otherwise.
        @rtype: boolean
        @raise ServiceError: If the paramName doesn't match with any parameter name a  L{ServiceError} is raised.
        """
        param = self.getParameter( paramName)
        if param :
            return param.ishidden()
        else:
            raise ServiceError , self._paramError + str( paramName )

    
    def iscommand(self ,paramName):
        """
        @param paramName: a parameter name
        @type paramName: String
        @return: True if this parameter is the command, False otherwise.
        @rtype: boolean
        @raise ServiceError: If the paramName doesn't match with any parameter name a  L{ServiceError} is raised.
        @call: by L{CommandBuilder.buildLocalCommand()<CommandBuilder>}
        """
        param = self.getParameter( paramName)
        if param :
            return param.iscommand()
        else:
            raise ServiceError , self._paramError + str( paramName )
                
    
    def issimple(self ,paramName):
        """
        @param paramName: a parameter name
        @type paramName: String
        @return: True if this parameter appear in the simple interface,
        False otherwise
        @rtype: boolean
        @raise ServiceError: If the paramName doesn't match with any parameter
        name a  L{ServiceError} is raised.
        """
        param = self.getParameter( paramName)
        if param :
            return param.issimple()
        else:
            raise ServiceError , self._paramError + str( paramName )


    def isout(self ,paramName):
        """
        @param paramName: a parameter name
        @type paramName: String
        @return: True if this parameter is an output of the program, False otherwise.
        @rtype: boolean
        @raise ServiceError: If the paramName doesn't match with any parameter
        name a  L{ServiceError} is raised.
        """
        param = self.getParameter( paramName)
        if param :
            return param.isout() 
        else:
            raise ServiceError , self._paramError + str( paramName )

    def isstdout( self ,paramName ):
        """
        @param paramName: a parameter name
        @type paramName: String
        @return: True if this parameter is the standard output of the program, False otherwise.
        @rtype: boolean
        @raise ServiceError: If the paramName doesn't match with any parameter
        name a  L{ServiceError} is raised.
        """
        param = self.getParameter( paramName)
        if param :
            return param.isstdout()
        else:
            raise ServiceError , self._paramError + str( paramName )

    def isInfile(self , paramName):
        """
        @param paramName: a parameter name
        @type paramName: String
        @return: True if this parameter should be transform in file (the parameter type is a Sequence or Text and isout is false).
        @rtype: boolean
        @raise ServiceError: If the paramName doesn't match with any parameter
        name a  L{ServiceError} is raised.
        """
        param = self.getParameter( paramName)
        if param :
            return param.isInfile()
        else:
            raise ServiceError , self._paramError + str( paramName )



    def isOutfile(self , paramName):
        """
        @param paramName: a parameter name
        @type paramName: String
        @return: True if the value of this parameter is a file(s) name (the parameter type is a Sequence or Text and isout is True).
        @rtype: boolean
        @raise ServiceError: If the paramName doesn't match with any parameter
        name a  L{ServiceError} is raised.
        """
        param = self.getParameter( paramName)
        if param :
            return param.isOutfile()
        else:
            raise ServiceError , self._paramError + str( paramName )


    def ismaininput(self , paramName ):
        """
        @param paramName: a parameter name
        @type paramName: String
        @return: True if the value of this parameter is a main input data.
        @rtype: boolean
        @raise ServiceError: If the paramName doesn't match with any parameter
        name a  L{ServiceError} is raised.
        """
        param = self.getParameter( paramName)
        if param :
            return param.ismaininput()
        else:
            raise ServiceError , self._paramError + str( paramName )
         
    
    def getMainInputs( self ): 
        """
        @return: the list of main input parameter names
        @rtype: list of strings
        """
        params = self._getAllParameter()
        mainInputs = [ param.getName() for param in params ]
        return mainInputs
  

    def getFormfield(self ,paramName):
        """
        @param paramName: a parameter name
        @type paramName: String
        @return: how the parameter will appear in the interface. ex in web interface formfield could be : checkbox, select ...
        @rtype: string
        @raise ServiceError: If the paramName doesn't match with any parameter name a  L{ServiceError} is raised.
        """
        param =self.getParameter( paramName)
        if param :
            return param.getFormfield()
        else:
            raise ServiceError , self._paramError + str( paramName )

        
    
    def getBioMoby(self ,paramName):
        """
        @param paramName: a parameter name
        @type paramName: String
        @return: the name of the corresponding object in the BioMoby-S ontology.
        @raise ServiceError: If the paramName doesn't match with any parameter
        name a  L{ServiceError} is raised.
        """
        param = self.getParameter( paramName)
        if param :
            return param.getBioMoby()
        else:
            raise ServiceError , self._paramError + str( paramName )


    def getPrompt(self , name, lang= None ):
        """
        @param name: a parameter or paragraph name
        @type name: String
        @param lang: the language of the prompt
        @type lang: should be String according to MNtoken iso639-1 (english='en' , french= 'fr ...)
        @return: the Prompt of the paragraph or the parameter. if there is no prompt for this parameter return None.
        @rtype: string or None
        @call: L{MobyleError.UserValueError}
        @raise ServiceError: If the paramName doesn't match with any parameter  name a  L{ServiceError} is raised.
        """
        para = self._getPara(name)
        if para :
            return para.getPrompt( lang )
        else :
            raise ServiceError, "this program does not containt neither parameter nor paragraph named: " + str(name)


    def promptLangs(self, name):
        """
        @param name: a parameter or paragraph name
        @type name: String
        @return: the list of language in which the prompt is written.
        @rtype: list of strings
        @call: L{Job}
        @call: L{MobyleError.UserValueError<UserValueError>}
        @raise ServiceError: If the paramName doesn't match with any parameter name a  L{ServiceError} is raised.
        """
        para = self._getPara(name)
        if para :
            return para.promptLangs()
        else :
            raise ServiceError, "this program does not containt neither parameter nor paragraph named: " + str(name)


    def promptHas_lang(self, name, lang):
        """
        @param name: a parameter or paragraph name
        @type name: String
        @param lang: the language in which is written the prompt
        @type lang: String
        @return: True if the prompt is written in lang, False otherwise.
        @rtype: boolean.
        @call: L{Job}
        @call: L{MobyleError.UserValueError<UserValueError>}
        @raise ServiceError: If the paramName doesn't match with any parameter name a  L{ServiceError} is raised.
        """
        para = self._getPara(name)
        if para :
            return para.promptHas_lang( lang )
        else :
            raise ServiceError, "this program does not containt neither parameter nor paragraph named: " + str(name)
        
        
    def setPrompt(self, name, prompt , lang='en'):
        """
        set the Prompt for the paragraph or the parameter
        @param name: a parameter or paragraph name
        @type name: String
        @param prompt: the paragraph or parameter prompt 
        @type prompt: String
        @param lang: the language of the prompt
        @type lang: should be String according to MNtoken iso639-1 (english='en' ,french= 'fr ...).
        @raise ServiceError: If the paramName doesn't match with any parameter name a  L{ServiceError} is raised.
        """
        ## n'est pas appele le parser appel directement les fonctions du paragraph ou du parameter
        para =self._getPara(name)
        if para :
            para.setPrompt( prompt, lang)
        else:
            raise ServiceError , "this program does not containt neither parameter nor paragraph named: " + str(name)



    def hasFormat(self, paramName):
        """
        @return: True if the  L{Parameter} has a format, False otherwise.
        @rtype: boolean.
        @raise ServiceError: If the name neither match with a parameter name nor a paragraph name, a  L{ServiceError} is raised.
        """
        para =self._getPara(paramName)
        if para :
            para.hasFormat( )
        else:
            raise ServiceError , "this program does not containt neither parameter nor paragraph named: " + str(paramName)


    def getFormat(self ,name, proglang):
        """
        If the name neither match with a parameter name nor a paragraph name, a  L{ServiceError} is raised.
        @param name: a parameter or paragraph name
        @type name: String
        @param proglang: the programming language in which the code is written
        @type proglang: string
        @return: the format
        @rtype: string
        @raise ServiceError: If the name neither match with a parameter name nor a paragraph name, a  L{ServiceError} is raised.
        """
        para = self._getPara(name)
        if para :
            return para.getFormat(proglang)
        else:
            return None

    def formatHas_proglang(self, name, proglang='python'):
        """
        @param name: a parameter or paragraph name
        @type name: String
        @param proglang: the name of a programming language.
        @type proglang: string.
        @return: True if a format written in proglang exist, False otherwise.
        @rtype: boolean.
        @raise ServiceError: If the name neither match with a parameter name nor a paragraph name, a  L{ServiceError} is raised.
        """
        para = self._getPara(name)
        if para :
            return para.formatHas_proglang( proglang )
        else :
            raise ServiceError, "this program does not containt neither parameter nor paragraph named: " + str(name)
       


    def formatProglangs(self, name):
        """
        @param name: a parameter or paragraph name
        @type name: String
        @return: A list containing the proglang used to encode the format.
        @rtype: list of strings.
        @raise ServiceError: If the name neither match with a parameter name nor a paragraph name, a  L{ServiceError} is raised.
        """
        para = self._getPara(name)
        if para :
            return para.formatProglangs()
        else :
            raise ServiceError, "this program does not containt neither parameter nor paragraph named: " + str(name)
       

    def setFormat(self, name, format , proglang="python"):
        """
        set the Format for the paragraph or the parameter according to the name 
        @param name: a parameter or paragraph name
        @type name: String
        @param format: the paragraph or parameter format 
        @type format: String
        @param proglang:
        @type proglang: String
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.
        """
        para =self._getPara(name)
        if para :
            para.setFormat( format, proglang)
        else:
            raise ServiceError , "this program does not containt neither parameter nor paragraph named: "+str(name)

  
    def getPreconds(self , name, proglang='python'):
        """
        @param name: a parameter or paragraph name
        @type name: String
        @param proglang:
        @type proglang: String
        @return: a list of string representing the preconds of the parameter or paragraph and 
            all preconds of parents paragraph in reverse order.
            if no precond could be found return []
        @rtype: list of strings .
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.
        @call: by L{Mobyle.CommandBuilder.buildLocalCommand}
        """
        para = self._getPara(name)
        if para :
            return para.getPreconds(proglang)
        else:
            return ServiceError , "this program does not containt neither parameter nor paragraph named: "+str(name)


    def precondHas_proglang(self, name, proglang):
        """
        @param name: a parameter or paragraph name
        @type name: String
        @param proglang: the programming language
        @type proglang: String
        @return: True if the precond is encoded in this programming language, False othewise
        @rtype: boolean.
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.
        """
        para = self._getPara(name)
        if para :
            return para.precondHas_proglang(proglang)
        else:
            return ServiceError , "this program does not containt neither parameter nor paragraph named: "+str(name)
        
        

    def precondProglangs(self , name):
        """
        If the name neither match with a parameter name nor a paragraph name, a  L{ServiceError} is raised.        
        @param name: a parameter or paragraph name
        @type name: String
        @return: a list of programming laguage in which the precond is encoded.
        @rtype: list of strings.
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.
        """
        para = self._getPara(name)
        if para :
            return para.precondProglangs()
        else:
            return ServiceError , "this program does not containt neither parameter nor paragraph named: "+str(name)

 

    def getVlist(self ,paramName,label):
        """
        @param paramName: the name of the parameter 
        @type paramName: A String
        @param label: a label of the vlist
        @type label: a String
        @return: the String representing value associated to this label.
        @rtype: string.
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.
        """
        param = self.getParameter( paramName)
        if param :
            return param.getVlist(label)
        else:
            raise ServiceError , self._paramError + str( paramName )


    def vlistLabels(self,paramName):
        """
        @param paramName: the name of the parameter 
        @type paramName: String
        @return: a list of String representing all the labels .
        @rtype: a list of strings.
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.        
        """
        param = self.getParameter( paramName)
        if param :
            return param.vlistLabels()
        else:
            raise ServiceError , self._paramError + str( paramName )


    def vlistHas_label(self, paramName,label):
        """
        @param paramName: the name of the parameter
        @type paramName: a String
        @return: True if the parameter with name paramName has a label == label
        False otherwise.
        @rtype: boolean.
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.
        """
        param = self.getParameter( paramName)
        if param :
            return param.vlistHas_label(label)
        else:
            raise ServiceError , self._paramError + str( paramName )


    def hasVlist(self, paramName):
        """
        @param paramName: the name of the parameter
        @type paramName: a String
        @return: Return True if the parameter has a vlist, False othewise.
        @rtype: boolean.
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.        
        """
        param = self.getParameter( paramName)
        if param :
            return param.hasVlist()
        else:
            raise ServiceError , self._paramError + str( paramName )


    def hasFlist(self, paramName):
        """
        @param paramName: the name of the parameter
        @type paramName: a String
        @return: True if the Parameter has a flist, False otherwise.
        @rtype: boolean.
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.        
        """       
        param = self.getParameter( paramName)
        if param :
            return param.hasFlist()
        else:
            raise ServiceError , self._paramError + str( paramName )


        
    def flistValues(self, paramName):
        """
        @param paramName: the name of the parameter
        @type paramName: a String.
        @return: a list of all values of the vlist
        @rtype: list of string.
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.        
        """
        param = self.getParameter( paramName)
        if param :
            return param.flistValues()
        else:
            raise ServiceError , self._paramError + str( paramName )



    def flistHas_value(self,paramName, value):
        """
        @param paramName: the name of the parameter
        @type paramName: a String
        @param value: the value to link the code to the label vlist
        @type value: integer
        @return: True if the the flist has a value == value, False otherwise.
        @rtype: boolean.
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.
        @raise UnDefAttrError: if the parameter hasn't flist a UnDefAttrError is raised
        """
        param = self.getParameter( paramName)
        if param :
            return param.flistHas_value( value )
        else:
            raise ServiceError , self._paramError + str( paramName )

                   

    def flistProglangs(self,paramName, value):
        """
        @param paramName: the name of the parameter
        @type paramName: a String        
        @param value:
        @type value:
        @return: the list of proglang available for a given value.
        @rtype: a list of strings.
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.
        @raise UnDefAttrError: if the parameter hasn't flist a L{UnDefAttrError} is raised
        """
        param = self.getParameter( paramName)
        if param :
            return param.flistProglangs( value )
        else:
            raise ServiceError, self._paramError + str( paramName )



    def flistHas_proglang(self,paramName , value , proglang):
        """
        @param paramName: the name of the parameter
        @type paramName: a String        
        @param value: the value associated to the codes
        @type value: any
        @param proglang: the programming language of the code
        @type proglang: String
        @return: Boolean, True if the flist has the value and a code written in proglang associated with, False otherwise.
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.
        @raise UnDefAttrError: if the parameter hasn't flist a UnDefAttrError is rais
        """
        param = self.getParameter( paramName)
        if param :
            return param.flistHas_proglang( value , proglang )
        else:
            raise ServiceError , self._paramError + str( paramName )

        
    def getFlistCode(self ,paramName, value, proglang):
        """
        @param paramName: the name of the parameter
        @type paramName: a String
        @param value: the value associated to the codes
        @type value: any
        @param proglang: the programming language of the code
        @type proglang: String
        @return: the code associated with the value and written in proglang. if there isn't this value or this proglang an Error is raised.
        @raise ServiceError: If the name neither match with a parameter name nor a paragraph name, a  L{ServiceError} is raised.
        @raise  L{ ServiceError}: if there isn't this value or this proglang an  L{ServiceError} is raised.
        """
        param = self.getParameter( paramName)
        if param :
            return param.getFlistCode(value, proglang)
        else:
            raise ServiceError , self._paramError + str( paramName )



    def getArgpos(self ,name):
        """
        If the name neither match with a parameter name nor a paragraph name, a  L{ServiceError} is raised.
        @param name: a parameter or paragraph name
        @type name: String
        @return: an int representing the argpos of a parameter or a paragraph
          if argpos isn't defined, return the argpos of the upper paragraph and so on.
          if no argpos could be found return 1
        @rtype: integer.
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.
        """
        para = self._getPara(name)
        if para:
            return para.getArgpos()
        else:
            raise ServiceError , self._paramError + str( name )
        
    def setArgpos(self, name,value):
        """
        set the argpos to value for the paragraph or the parameter

        @param name: A parameter or paragraph name.
        @type name: String.
        @param value: The argpos.
        @type value: Integer.
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.
        """
        para = self._getPara(name)
        if para:
            para.setArgpos(value)
        else:
            raise ServiceError, "this program does not containt neither parameter nor paragraph named: "+str(name)

    def has_ctrl(self,paramName):
        """
        @param paramName: the name of the parameter
        @type paramName: String         
        @return: True if the parameter has  L{Ctrl}, False otherwise.
        @rtype: boolean.
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.
        """
        param = self.getParameter( paramName)
        if param :
            return param.has_ctrl()
        else:
            raise ServiceError , self._paramError + str( paramName )
        

    def getCtrls(self ,paramName):
        """
        If the paramName doesn't match with any parameter name a  L{ServiceError} is raised.
        @param paramName: the name of a parameter
        @type paramName: String
        @return: a list of  L{Ctrl} instances for the parameter.
        @rtype: [ L{Ctrl} instances,...]
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.
        """
        param = self.getParameter( paramName)
        if param :
            return param.getCtrls()
        else:
            raise ServiceError , self._paramError + str( paramName )

    def doCtrls(self , paramName):
        """
        do the controls specific to the parameter paramName
        @return: if the control are Ok return True other wise a UserValueError is raised.
        @rtype ???: a determiner doit retourner false ou lever une erreur ???? 
        @raise ServiceError: If the name neither match with a parameter name nor a paragraph name, a  L{ServiceError} is raised.
        """
        param = self.getParameter( paramName)
        if param :
            return param.doCtrls()
        else:
            raise ServiceError , self._paramError + str( paramName )
       
    def hasParamfile(self ,paramName):
        """
        @param paramName: the name of the parameter
        @type paramName:  String
        @return: True if the parameter should be specified in a file
        instead the command line, False otherwise
        @rtype: boolean.
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.
        """
        param = self.getParameter( paramName)
        if param :
            return param.hasParamfile()
        else:
            raise ServiceError , self._paramError + str( paramName )


    def getParamfile(self ,paramName):
        """
        @param paramName: the name of the parameter
        @type paramName:  String
        @return: the name of the parameter file. if the parameter must be
        specified in a file instead on the command line.
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.
        @raise UnDefAttrErrorError: If the parameter haven't a paramfile an  L{UnDefAttrErrorError} is raised.
        """
        param = self.getParameter( paramName)
        if param :
            return param.getParamfile()
        else:
            raise ServiceError , self._paramError + str( paramName )


    def getAllFileNames(self, proglang = 'python'):
        """
        @param proglang: the programming language used to defined the filenames
        @type proglang: string
        @return: The unix mask ( *.dnd ) which permit to retrieve the results files.
        @rtype: list of strings. If there isn't any fileName return an empty list
        """
        outParameters = self.getAllOutParameter()
        result=[]
        for parameter in outParameters:
            try:
                filenames = self.getFilenames(parameter, proglang = 'python')
                for  filename in filenames:
                    if filename  not in result:
                        result.append( filename )
            except UnDefAttrError:
                continue
        return result


    
    def getFilenames(self ,paramName, proglang = 'python'):
        """
        @param paramName: the name of the parameter
        @type paraName: String
        @param proglang: the programming language used to defined the filenames
        @type proglang: string
        @return: The unix mask ( *.dnd ) which permit to retrieve the results files.
        @rtype: string.
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.
        @call: RunnerFather to fill the 4Child.dump structure 
        @call: Core in validate method of all "file" parameter
        """
        param = self.getParameter( paramName)
        if param :
            return param.getFilenames( proglang )
        else:
            raise ServiceError , self._paramError + str( paramName )


    def hasScale( self , paramName , proglang = 'python' ):
        """
        @return: True if the param has a scale with code in proglang or with value, False otherwise. 
        @rtype: boolean
        """
        param = self.getParameter( paramName)
        if param :
            return param.hasScale( proglang= proglang )
        else:
            raise ServiceError , self._paramError + str( paramName )
        


    def isInScale( self , paramName , proglang = 'python'):
        """
        @return: True if the value is in range(min, max), false otherwise
        @rtype: boolean
        """
        param = self.getParameter( paramName)
        if param :
            return param.isInScale( proglang= proglang )
        else:
            raise ServiceError , self._paramError + str( paramName )
        
    def getScale(self , paramName , proglang= None):
        """
        @param paramName: the name of the parameter
        @type paramName: String
        @param proglang: the programming language if the scale is defined by codes. if proglang = None, it mean that the scale is defined by values .
        @type proglang: String
        @return: a tuple (min,max,inc)
          -min is either a value if proglang =None or a code if proglang is specified
          -max is either a value if proglang =None or a code if proglang is specified
          -inc is a value
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.
        """
        param = self.getParameter( paramName)
        if param :
            return param.getScale(proglang= proglang)
        else:
            raise ServiceError , self._paramError + str( paramName )


    def getSeparator(self ,paramName):
        """
        @param paramName: the name of the parameter
        @type paramName: String
        @return: the string used to separate the differents values of a mutipleChoice vlist.
        @rtype: string
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.
        """
        param = self.getParameter( paramName)
        if param :
            return param.getSeparator()
        else:
            raise ServiceError , self._paramError + str( paramName )


    def getWidth(self ,paramName):
        """
        @param paramName: the name of the parameter
        @type paramName: String
        @return: the width of the widget.
        @rtype: integer
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.
        """
        param = self.getParameter( paramName)
        if param :
            return param.getWidth()
        else:
            raise ServiceError , self._paramError + str( paramName )


    def getHeight(self ,paramName):
        """
        @param paramName: the name of the parameter
        @type paramName: String
        @return: The height of the widget.
        @rtype: integer
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.
        """
        param = self.getParameter( paramName)
        if param :
            return param.getHeight()
        else:
            raise ServiceError , self._paramError + str( paramName )

        
    def getExemple(self ,paramName):
        """
        @param paramName: the name of the parameter
        @type paramName: String
        @return: A typical value for this parameter
        @rtype: string
        @raise ServiceError: If the name neither match with a parameter
        name nor a paragraph name, a  L{ServiceError} is raised.
        """
        param = self.getParameter( paramName)
        if param :
            return param.getExemple()
        else:
            raise ServiceError , self._paramError + str( paramName )



    def getEvaluator(self):
        """
        @return: a reference toward the  L{Evaluation} instance link to this program.
        @rtype:  L{Evaluation object}
        """
        return self._evaluator


    def setEvaluator(self, evaluator):
        """
        """
        self._evaluator = evaluator
        paras = self._parameters.getAllParagraph()
        paras += self._parameters.getAllParameter()
        for para in paras:
            para.setEvaluator( evaluator)
            
    def isProgram(self):
        """
        @return: True
        """
        return True

    def getFather(self):
        """
        @return: None. A program have no father
        it's used as stopping condition when a child want to retrieve the program
        """
        return None    


    
#############################################################
#                                                           #
#                Class Parameters                           #
#                                                           #
#############################################################

class Parameters(object):
    """the parameters objects are mainly used to managed the
    parameter and paragraph"""
    

    def __init__(self):
        self._paragraphList= []
        self._parameterList= []
        self._info = Text()
        
    def addParagraph(self, paragraph):
        """
        add a paragraph instance into this parameters
        @param paragraph: the pargraph to add
        @type paragraph: a Paragraph object
        """
        self._paragraphList.append( paragraph )

    def addParameter(self, parameter):
        """
        add a parameter instance into this parameters
        @param parameter: the parameter to add
        @type parameter: a Parameter object
        """
        self._parameterList.append( parameter )



    def getParagraph(self, paragraphName):
        """
        @param paragraphName: the name of a paragraph to retrieve
        @type paragraphName: String
        @return: the instance of the  L{Paragraph} which has the name paragraphName. if no pragraph is found, return None.
        @rtype:  L{Paragraph} object or None
        """
        result = None
        for paragraph in self._paragraphList:
            if paragraph.getName() == paragraphName:
                return paragraph
            else:
                result = paragraph.getParagraph(paragraphName)
                if result:
                    return result
        return None



    def getParameter(self, parameterName):
        """
        @param parameterName: the name of a parameter to retrieve
        @type parameterName: String
        @return: the instance of the  L{Parameter} which has the name parameterName. if no parameter is found, return None.
        @rtype:  L{Parameter} object or None
        """
        for parameter in self._parameterList:
            if parameter.getName() == parameterName :
                return parameter
        result = None
        for paragraph in self._paragraphList:
            result = paragraph.getParameter(parameterName)
            if result:
                return result
        return None

    def getAllParagraph(self):
        """
        @return: all paragraphs instances in a list.
        @rtype: list of L{paragraphs <Paragraph>} object.
        """
        allParagraph = self._paragraphList[:]
        for paragraph in self._paragraphList:
            allParagraph += paragraph.getAllParagraph()
        return allParagraph

    
    def getAllParameter(self):
        """
        @return: all L{parameter <Parameter>} instances in a flat list.
        @rtype: list of parameter object.
        """
        allParameter = self._parameterList[:]
        for paragraph in self._paragraphList:
            allParameter += paragraph.getAllParameter()
        return allParameter
        

    #getPath ne devrait pas etre appelee directement mais par
    #l'intermedaire de getPath du program ou du paragraph

    def getPath(self,parent, name):
        """
        @param parent: the parent of the paragraph or the program
        @type parent: a  L{Paragraph} instance or a  L{Program} instance
        @param name: the name of the paragraph or parameter
        @type name: String
        @return:  the path each name is separated by '/'
        @rtype: string
        """
        for para in self._thisLevel():
            if para.getName() == name :
                return parent.getName()+"/"+ name
        result = None
        for paragraph in self._paragraphList:
            result = paragraph.getPath(name)
            if result:
                return parent.getName()+"/"+ result
        return None




    def addInfo(self, content, proglang = None , lang = None , href = False):
        """
        Set an help on this program
        @param content: an help on the program or a href toward an help
        @type content: String
        @param proglang: is the symbol of a lang in iso639-1 (ex: 'en', 'fr') for the text or 'href' for the link
        @type proglang: String
        @param href: True if the content is a href false otherwise
        @type href: boolean
        @raise ServiceError: if more than one argument among proglang, lang, href is specified a L{ServiceError} is raised
        """
        if ( (proglang and lang) or (proglang and href) or (lang and href) ):
            raise ServiceError, "an info couldn't be a text and a code or href at the sametime"
        if proglang:
            self._info.addCode( content , proglang= proglang)
        elif lang:
            self._info.addText( content , lang = lang)
        elif href:
            self._info.addHref( content)
        else :
            raise ServiceError, "invalid argument for info : " + proglang + lang + href
        

        
    def getInfo(self, proglang =None, lang = None , href = False):
        """
        @param lang: is the symbol of a lang in iso639-1 (ex: 'en', 'fr') for the text or 'href' for the link
        @type lang: String
        @param proglang: is the symbol of a lang in iso639-1 (ex: 'en', 'fr') for the text or 'href' for the link
        @type proglang: String
        @param href: True if the content is a href false otherwise
        @type href: Boolean
        @return: the info corresponding to the specified lang or proglang or href.
        @rtype: string
        @raise ServiceError: if more than one argument among proglang, lang, href is be specified a L{ServiceError} is raised
        @raise MobyleError: a  L{MobyleError} is propagated  if there isn't any code written in proglang or text in lang or if href is true and it's not a href
        """
        if ( (proglang and lang) or (proglang and href) or (lang and href) ):
            raise ServiceError, "the info couldn't be a text and a code or a href at the same time"
        if proglang:
            return self._info.getCode( proglang)
        elif lang:
            return self._info.getText( lang)
        elif href:
            return self._info.hrefs( )
        else :
            raise ServiceError, "invalid argument for info : " +str(lang)+" , "+str(proglang)+" , "+str(href)

               
    def infoHas_proglang(self, proglang = 'python'):
        """
        @return: True if the info is encoded in the programming language proglang, False otherwise.
        @rtype: boolean.
        """
        return self._info.has_code( proglang)

    def infoProglangs(self):
        """
        @return: the list of programming languages used for the info codes
        @rtype: list of string.
        """
        return self._info.proglangs()

    def infoHas_lang(self, lang='en'):
        """
        @return: True if the info has a text written in lang. False otherwise.
        @rtype: boolean.
        """
        return self._info.has_lang(lang)
        

    def infoLangs(self):
        """
        @return: the list of langs used for the info texts.
        @rtype: list of strings
        """
        return self._info.langs()
         

    def infoHas_href(self):
        """
        @return: True if the info has a 'href', False otherwise.
        @rtype: boolean
        """
        return self._info.has_href() 
    

    def _thisLevel(self):
        """
        @return: all paragraph and parameter of this level in a list
        @rtype: list of L{Para} instances
        """
        return self._parameterList[:]+ self._paragraphList[:]
        
       
#    def isProgram(self):
#        return False
        
############################################################
#                                                          #
#                  Class header                            #
#                                                          #
############################################################
class Header(object):
    def __init__(self ):
        self._name = ""   
        self._url = "" 
        self._version = ""
        self._title = ""
        self._doclinks   = []
        self._categories = []
        self._command    = ('' , '' , '') #will be a tuple like (name, type, path)
        self._env        = {}
        self._help        = Text()


        
    def setTitle(self, value):
        """
        set the title of the Program
        @param value: the Program title
        @type value: String
        """
        try:
            value + "a"
            self._title= value
        except TypeError:
            raise ServiceError , "the title must be a String"

        
    def getTitle(self):
        """
        @return: a String representing the  L{Program} title
        @rtype: string
        """ 
        return self._title
    
    def setUrl(self , url ):
        """
        @param url: the url of this Program definition
        @type url: string
        """
        self._url = url
        
    def getUrl(self):
        """
        @return: the url of the definition of this Program
        @rtype: string
        """
        return self._url
    
    
    def setName(self, value):
        """
        set the name of the L{Program} to value
        @param value: the L{Program} name
        @type value: String
        """
        try:
            value + "a"
            self._name = value
        except TypeError:
            raise ServiceError , "the name must be a String"
        
    def getName(self):
        """
        @return: a String resprenting the name of the L{Program}.
        @rtype: string
        """
        return self._name
        
             
    def setVersion(self, value):
        """
        set the version of the program
        @param value: the version of the program
        @type value: String
        """
        self._version = value
             
    def getVersion(self):
        """
        @return: a String representing the version of the program
        @rtype: string
        """
        return self._version
        
    def addDoclink(self, values):
        """
        Add a link toward a documentation
        @param values:
        @type values: a list or a tuple of Strings
        """
        if type(values) == type([]) or type(values) == type( () ):
            self._doclinks += values
        else:
            self._doclinks.append( values )

        
    def getDoclinks(self):
        """
        @return: a list of Strings. Each String represent a documentation link
        """
        return self._doclinks


    def addHelp(self, content, proglang = None , lang = None , href = False):
        """
        Set an help on this Program. Only one of the arguments proglang, lang or href must be specified. If more than one arguments among these are specified, a  L{ServiceError} is raised.
        @param content: an help on the Program or a href toward an help
        @type content: String
        @param proglang: The programming language of the help code
        @type proglang: String
        @param lang: is the symbol of a lang in iso639-1 (ex: 'en', 'fr') for the text 
        @type lang: String
        @param href: True if the content is a href false otherwise
        @type href: boolean
        """

        if ( (proglang and lang) or (proglang and href) or (lang and href) ):
            raise ServiceError, "an help couldn't be a text and a code or href at the same time"
        if proglang:
            self._help.addCode( content , proglang)
        elif lang:
            self._help.addText( content , lang)
        elif href:
            self._help.addHref( content)
        else :
            raise ServiceError, "invalid argument for help : " + proglang + lang + href
        
        

    def getHelp(self, lang = None, proglang =None , href = False):
        """
        Only one of the arguments proglang, lang or href must be specified. If more than one arguments among these are specified, a  L{ServiceError} is raised.
        @param proglang: The programming language of the help code
        @type proglang: String
        @param lang: is the symbol of a lang in iso639-1 (ex: 'en', 'fr') for the text 
        @type lang: String
        @param href: True if the content is a href false otherwise
        @type href: boolean
        @return: the help corresponding to the specified lang or proglang or href
        @rtype: string.
        """

        if ( (proglang and lang) or (proglang and href) or (lang and href) ):
            raise ServiceError, "an help couldn't be a text and a code or href in the same time "
        if proglang:
            return self._help.getCode( proglang)
        elif lang:
            return self._help.getText( lang)
        elif href:
            return self._help.hrefs( )
        else :
            raise ServiceError, "invalid argument for help : " +str(lang)+" , "+str(proglang)+" , "+str(href)


               
    def helpHas_proglang(self, proglang = 'python'):
        """
        @param proglang: the programming language that encode the help
        @type proglang: String
        @return: True if a code written in proglang is used for the help,
        False otherwise.
        @rtype: boolean.
        """
        return self._help.has_proglang( proglang)

    def helpProglangs(self):
        """
        @return: the list of proglangs used for the code help.
        @rtype: list of string.
        """
        return self._help.proglangs()

    def helpHas_lang(self, lang='en'):
        """
        @return: True if the help has a text written in lang. False otherwise
        @rtype: boolean.
        """
        return self._help.has_lang(lang)
        

    def helpLangs(self):
        """
        @return: the list of langs used for the help texts.
        @rtype: a list of string
        """
        return self._help.langs()
         

    def helpHas_href(self):
        """
        @return: True if the help has a 'href', False otherwise.
        @rtype: boolean
        """
        return self._help.has_href() 

        
    def helpHrefs(self):
        """
        @return: The list of href for the help.
        @rtype: list of string 
        """
        return self._help.hrefs()

        
    def setCommand(self, name, type='local', path=None):
        """
        set the name, the  type and the path of the command
        @param name:
            1. for local program: is the name of the program
            2. for cgi: is the name of the cgi
            3. for web Program: is the name of the method
        @type name: String
        @param type:
            1. for local program: is 'local' (by default)
            2. for cgi: is the method to call the cgi ( GET | POST | POSTM )
            3. for web Program: is the protocol to call the ws (soap | xml-rpc | ... )
        @type type: String
        @param path:
            1. for local program: is the path where is the program (by default the $PATH variable)
            2. for cgi: is the url where is the script 'http://www.myDomain.org'
            3. for web Program: is the url of the wsdl
        @type path: String
        """
        self._command = ( name, type, path )

        
    def getCommand(self):
        """
        @return: (name, type , path)
          1. for local program:
              - name is the name of the program
              - type is 'local' (by default)
              - path is the path where is the program (by default the $PATH variable) 
          2. for cgi:
              - name is the name of the cgi
              - type is the method to call the cgi ( GET | POST | POSTM )
              - path is the url where is the script 'http://www.myDomain.org'
          3. for web Program:
              - name is the name of the method
              - type is the protocol to call the ws (soap | xml-rpc | ... )
              - path is the url of the wsdl
        @rtype: tuple of 3 string (name, type, path).
        @call: L{CommandBuilder.BuildLocalCommand<CommandBuilder>}
        """
        return self._command


    def addEnv(self, var, value):
        """
        add an variable environment need to run the programm
        @param var: the name of the variable
        @type var: String
        @param value: the value of the environment variable
        @type value: String
        """
        self._env[ var ] = value


    def getEnv(self, varName):
        """
        @param varName: the name of the environment variable.
        @type varName: String
        @return: the value of the environment variable,  if there is no environment variable return None.
        @rtype: string or None
        @call: L{CommandBuilder.BuildLocalCommand<CommandBuilder>}
        """
        if self._env:
            try:
                return self._env[ varName ]
            except KeyError:
                return None
        else:
            return None

    def envHas_var(self, var):
        """
        @param var: the name of the environment variable
        @type var: String
        @return: True the variable var is specified, False otherwise.
        @rtype: boolean.
        """
        return self._env.has_key(var)
    
    def envVars(self):
        """
        @return: the names of all environment variables.
        @rtype: string
        @call: L{CommandBuilder.BuildLocalCommand<CommandBuilder>}
        """
        return self._env.keys()
    

    def addCategories(self, values):
        """
        add a category or sequence of categories in categories
        @param values: a category or a sequence of categories.
        @type values: String or Strings sequence.
        """
        #if values is a list or a tuple of categories
        if type(values) == type([]) or type(values) == type( () ):
            self._categories += values
        else:
            self._categories.append(values)

            
    def getCategories(self):
        """
        @return: the list of String, each string representing
        a category in which the Program is classified.
        @rtype: a list of String
        """
        return self._categories


############################################################
#                                                          #
#                 abstract Class Para                      #
#                                                          #
############################################################


class Para(object):
    """
    This class is abstract thus it should never be instanciate.
    The class Para is used to group the attributes and 
    shared methods by parameters and paragraph together.
    """
    def __init__(self, evaluator ):
        self._debug = None
        self._father = None
        self._evaluator = evaluator
        self._name = None
        self._argpos = None
        self._prompt = {}
        self._precond = {}
        self._format = {}

    def __str__(self):
        if self._name:
            return self._name
        else:
            return repr( self )

    def setName(self, value):
        """
        set the name of the paragraph or parameter to value.
        Two paragraphs or parameter can't have the same name
        @param value: the name of the paragraph or parameter
        @type value: String
        """
        self._name = value

        
    def getName(self):
        """
        @return: The name of this para(graph or meter)
        @rtype: string
        """
        return self._name

    
    def getArgpos(self ):
        """
        @return: the argpos for the paragraph or parameter
         - if argpos isn't defined, return the argpos of the upper paragraph and so on.
         - if no argpos could be found, return 1
        @rtype: number 
        """
        if self._argpos != None :
            return self._argpos
        else:
            if self._father.isProgram():
                return 1 
            else:
                return self._father.getArgpos()

    
    
    def getDebug(self ):
        """
        @return: the debug level
        @rtype: int
        """
        if self._debug is None :
            debug = self._father.getDebug()
            if debug is None:
                debug = 0
            self._debug = debug
        return self._debug
           
    
    def setArgpos(self, value):
        """
        set the argpos to value for this paragraph or parameter
        @param value: the argpos value
        @type value: Integer
        """
        try:
            value + 3
            self._argpos = value
        except TypeError:
            raise ServiceError , "argpos must be a number"


    def addPrompt(self, value, lang="en"):
        """
        add a prompt to this parameter or paragraph
        @param value: the prompt to add
        @type value: String
        @param lang: the laguage encoding the prompt: it should be iso639-1 compliant
        @type lang: String
        """
        self._prompt[ lang ] = value


    def getPrompt(self, lang = None):
        """
        @param lang: the laguage encoding the prompt: it should be iso639-1 compliant
        @type lang: String
        @return: The prompt. if there is no prompt , return None
        @rtype: string
        """
        if not lang:
            lang =_cfg.lang()
        try:
            return self._prompt[ lang ]
        except KeyError:
            return None

    def promptLangs(self):
        """
        @return: the list of language in which the prompt is written.
        @rtype: string
        """
        return self._prompt.keys()

    def promptHas_lang(self,lang):
        """
        @param lang: the language in which is written the prompt
        @type lang: String
        @return: True if the prompt is written in lang, False otherwise.
        @rtype: boolean.
        """
        return self._prompt.has_key( lang )
        

    def getPreconds(self , proglang= 'python' ):
        """
        @param proglang: the programming language which encode the precond
        @type proglang: String
        @return: the list of precond in reverse order. If no precond could be found return [].
        @rtype: list of string
        """
        preconds = []
                 
        father = self.getFather()
        if not father.isProgram():
            prec = father.getPreconds( proglang = proglang )
            preconds += prec
        if self._precond:
            pc = self._precond[proglang]
            if pc:
                preconds += pc 
        return preconds
                
                
    def addPrecond(self, precond, proglang='python'):
        """
        add a precond for this paragraph or parameter. Be carful if a precond with the same prolang already exist it will be replace by this one
        @param precond: the precond to add
        @type precond: String
        @param proglang: the encoding language for the precond
        @type proglang: String
        """
        precond = precond.strip() 
        if self._precond.has_key( proglang ):
            self._precond[ proglang ].append( precond )
        else:
            self._precond[ proglang ]= [ precond ]
            
    def precondHas_proglang(self, proglang):
        """
        @param proglang: the programming language
        @type proglang: String
        @return: True if the precond is encoded in this programming language, False othewise.
        @rtype: boolean.
        """
        if self._precond:
            return self._precond.has_key(proglang)
        else:
            if self._father.isProgram():
                return None
            else:
                return self._father.precondHas_proglang( proglang )

    def precondProglangs(self):
        """
        @return: a list of programming laguage in which the precond is encoded.
        @rtype: list of string.
        """
        if self._precond:
            return self._precond.keys()
        else:
            if self._father.isProgram():
                return None
            else:
                return self._father.precondProglangs()


    def hasFormat(self):
        """
        @return: True if the  L{Parameter} has a format, False otherwise
        @rtype: boolean
        """
        if self._format:
            return True
        else:
            return False


    def getFormat(self , proglang):
        """
        @param proglang: the programming language which encode the format
        @type proglang: String.
        @return: the format
        @rtype: string
        """
        try:
            return self._format[proglang]
        except KeyError:
            raise ServiceError, "no format for this proglang: "+proglang


    def formatProglangs(self):
        """
        @return: a list of programming languages.
        @rtype: string
        """
        return self._format.keys()


    def formatHas_proglang(self, proglang='python'):
        """
        @param proglang: the name of a programming language.
        @type proglang: string.
        @return: True if a format written in proglang exist, False otherwise.
        @rtype: boolean
        """
        return self._format.has_key(proglang)

     
    def addFormat(self, format, proglang):
        """
        add a format to this parameter or paragraph
        @param format: the format to add
        @type format: String
        @param proglang: the programming language that encode the format
        @type proglang: String
        """
        self._format[proglang] = format.strip()
        

    def isProgram(self):
        """
        @return: False.
        @rtype boolean
        """
        return False

    def setFather(self,father):
        """
        set the father of this paragraph or the paragraph or program at the upper level
        @param father: is a reference to the instance of the paragraph or program at the upper level
        @type father: a  L{Program} or  L{Paragraph} instance"""
        self._father = father
        

    def getFather(self):
        """
        @return: a reference toward the instance of the paragraph or program at the upper level
        @rtype: a L{Paragraph} or a L{Program} object
        """
        return self._father    
    
    
    def getProgram(self):
        program = self.getFather()
        while program is not None and not program.isProgram():
            program = program.getFather()
        return program
    
    def setEvaluator(self, evaluator):
        """
        set the evaluator of this paragraph. it's a reference toward the program's evaluator.
        @param evaluator: is a reference to the instance of the paragraph or program at the upper level
        @type evaluator: a  L{Evaluation} instance
        """
        self._evaluator = evaluator

       
    def getEvaluator(self):
        """
        @return: a reference toward the instance of the  L{Evaluation} instance of the program.
        @rtype:  L{Evaluation} object.
        """
        return self._evaluator    
    
   
############################################################
#                                                          #
#                  Class Paragraph                         #
#                                                          #
############################################################


class Paragraph(Para):

    def __init__( self , evaluator ):
        Para.__init__(self , evaluator )
        self._layout = []
        self._parameters = Parameters()
        
            
    def getParameters(self):
        """
        @return: the -L{Parameters} instance 
        @rtype: Parameters object
        """
        return self._parameters
    
    def getParagraph(self, paragraphName):
        """
        @param paragraphName: the name of the paragraph to retrieve
        @type paragraphName: String
        @return: the instance of  L{Paragraph} in this paragraph or
        in lower paragraph and which have the name parameterName.
        @rtype: Paragraph object or None.
        """
        return self._parameters.getParagraph(paragraphName)

    def addParameter(self, parameter):
        """
        add a parameter to this paragraph. The added parameter
        will be at a lower level
        @param parameter: the parameter to add
        @type parameter: A Parameter Instance
        """
        self._parameters.addParameter(parameter)
        parameter.setFather(self)
        parameter.setEvaluator(self._evaluator)

            
    def addParagraph(self, paragraph):
        """
        add a paragraph to this paragraph the added paragraph
        will be at a lower level
        @param paragraph: the paragraph to add
        @type paragraph: A Paragraph instance
        """
        self._parameters.addParagraph(paragraph)
        paragraph.setFather(self)
        paragraph.setEvaluator(self._evaluator)
                   
        
    def getParameter(self, parameterName):
        """
        @param parameterName: the name of the parameter to retrieve
        @type parameterName: String
        @return: the instance of  L{Parameter} in this paragraph
        or in lower paragraph and which have the name parameterName
        @rtype:  L{Parameter} object or None
        """
        return self._parameters.getParameter(parameterName)
      


    def getAllParagraph(self):
        """
        @return: all  L{Paragraph} instances in this paragraph
        @rtype: list of  L{Paragraph} instances
        """
        return self._parameters.getAllParagraph()
        
    def getAllParameter(self):
        """
        @return: all  L{Parameter} instances in this paragraph.
        @rtype: list of  L{Parameter} instances
        """
        return self._parameters.getAllParameter()
        

    def getPath(self,name):
        """
        @param name: the name of a parameter or paragraph
        @type name: String
        @return: the path of this paragraph
        it have the form    program/paragraph1/paragraph2/...[parameter]
        @rtype: string
        """
        return self._parameters.getPath(self,name)

    
    def addInfo(self, content, proglang = None , lang = None , href = False):
        """
        Set an info on this paragraph
        Only one of the arguments proglang, lang or href must be specified. If more than one arguments among these are specified, a  L{PargraphError} is raised.
        @param content: an info on the program or a href toward an info
        @type content: String
        @param proglang: the programming language of the info code
        @type proglang: String
        @param lang: is the symbol of a language in  iso639-1 (ex:english= 'en',french= 'fr') 
        @type lang: String
        @param href: True if the content is a href, False otherwise
        @type href: Boolean
        """
        if ( (proglang and lang) or (proglang and href) or (lang and href) ):
            raise ServiceError, "an info couldn't be a text and a code or href in the same time"
        if proglang:
            self._parameters.addInfo( content , proglang = proglang)
        elif lang:
            self._parameters.addInfo( content , lang = lang)
        elif href:
            self._parameters.addInfo( content )
        else :
            raise ServiceError, "invalid argument for info : " + proglang + lang + href
        
        

    def getInfo(self, proglang =None ,lang= None, href = False):
        """
        Only one of the arguments proglang, lang or href must be specified. If more than one arguments among these are specified, a  L{ServiceError} is raised.
        @param proglang: The programming language of the info code
        @type proglang: String
        @param lang: is the symbol of a language in iso639-1 (ex: 'en', 'fr') for a text info
        @type lang: String
        @param href: True if the info is a href, False otherwise
        @type href: Boolean
        @return: the info corresponding to the specified lang, proglang or href
        @rtype: string
        """
        if ( (proglang and lang) or (proglang and href) or (lang and href) ):
            raise ServiceError, "an info couldn't be a text and a code or a href in the same time "
        if proglang:
            return self._parameters.getInfo( proglang = proglang)
        elif lang:
            return self._parameters.getInfo( lang = lang)
        elif href:
            return self._parameters.getInfo( )
        else :
            raise ServiceError, "invalid argument for info : " +str(lang)+" , "+str(proglang)+" , "+str(href)

               
    def infoProglangs(self):
        """
        @return: the list of programming languages used by the info codes.
        @rtype: string.
        """
        return self._parameters.infoProglangs()

    def infoHas_lang(self, lang='en'):
        """
        @param lang: the symbol of a language in iso639-1 (ex: 'en', 'fr') 
        @type lang: String
        @return: True if the info has a text written in lang, False otherwise.
        @rtype: boolean
        """
        return self._parameters.infoHas_lang( lang= lang)
        

    def infoLangs(self):
        """
        @return: the list of languages used by the info texts.
        @rtype: list of string.
        """
        return self._parameters.infoLangs()
         

    def infoHas_href(self):
        """
        @return: True if the info has a 'href', False otherwise.
        @rtype: boolean
        """
        return self._parameters.infoHas_href() 
        



        
############################################################
#                                                          #
#                  Class Parameter                         #
#                                                          #
############################################################
        
class Parameter( Para ):
    """
    Parameter is an abstract class which contains all the attributes
    and methods common to all parameter subclass
    while the class in core.py are the subclass and provide the specific
    methods 
    """
    def __init__(self, mobyleType , evaluator = None , name = None , value=None ):
        self._mobyleType = mobyleType
        if evaluator is None:
            evaluator =Evaluation()
        self.cfg = Config()
        Para.__init__(self, evaluator )
        self._name = name
        self._ismandatory = False
        self._ishidden = False
        self._iscommand = False
        self._isstdout = False
        self._issimple = False # encore d'actualite ??
        self._formfield = ""
        self._isout = False
        self._ismaininput = False
        self._width = None
        self._height = None
        self._separator = None
        self._filenames = {} #the keys are programming language, the values are list of strings
        self._paramfile = ""
        self._scalemin = {}           #the keys is 'value' or a proglang
        self._scalemax = {}           #the values will be a value or a code
        self._scaleinc = None 
        self._vlist = {}    #????????????????????
        self._flist = {}    #with value as key
        self._undefValue = None
        self._ctrls = []    # a ctrl list
        self._vdef = None  
        if value is not None:
            if self._name is not None:
                self.setValue( value )
            else:
                raise MobyleError , "if value is specified name must be specified"
        
    def ancestors( self ):
        #1 exclude the parameter self.__class__.__name__ itself
        #-3 exclude "Parameter" , "Para" , and "object"
        return [ k.__name__ for k in self.__class__.mro()][1:-3]

    def getValue( self ):
        """
        @return: the current value for this parameter.
        If value is not defined return None
        @rtype: any
        @call: Program.getValue
        """
        evaluator = self.getEvaluator()
        return evaluator.getVar( self.getName() )
    
    
        
    def setValue( self , value ) :
        """
        set the current value for this parameter and put it in the evaluation pace.
        if the value doesn't match with the parameter's class a UserValueError is
         thrown
        the SequenceParameter can throws an UnsupportedFormatError if the output
         format is nos supported or a MobyleError if something goe's wrong during
         the conversion
        @param value: the value  of this parameter
        @type value: any builtin classes (in core.py) or an instance of a class defined by user in ../Classes
        @call: Program.setValue
        """
        if self.ishidden():
            raise MobyleError , "the parameter %s is hidden, it's value cannot be changed" % self.getName()
        elif self.isout():
            raise MobyleError , "the parameter %s is out, it's value cannot be changed" % self.getName()
        else:
            if value is not None:
                if self._separator is not None:
                    #if separator is not None the Datatype is a MultipleChoice.
                    #the argument value is a list
                    #the value in the evaluator must be the final string
                    value = self._separator.join( value )
                self.getEvaluator().setVar( self.getName() ,  value  )
                
            else:
                self.getEvaluator().setVar( self.getName() , None )
                

    def setValueAsVdef( self ):
        """
        get the vdef and setValue with it
        """
        if self.isInfile():
            raise MobyleError , "an infile parameter can't have vdef"
        vdef = self.getVdef()
        if vdef is None :
            self.getEvaluator().setVar( self.getName() , None )
        else:
            self.getEvaluator().setVar( self.getName() , self.convert( vdef ) )

    def renameFile( self,  workdir , newName ):
        """
        rename a parameter File, rename the file on the filesystem and chage the value in Evaluator
        @param workdir: the absolute path to the job directory (where to find the file
        @type workdir: string
        @param newName:the file name to rename in the workdir
        @type newName: string
        """
        if self.isInfile():
            try:
                os.rename( os.path.join( workdir , self.getValue() ) , os.path.join( workdir , newName ) )
                self.getEvaluator().setVar( self.getName() , newName )
            except IOError , err:
                raise MobyleError , 'Cannot rename the file corresponding to %s parameter :%s'%(  self.getName(),
                                                                                                 err)
        else:
            s_log.error( 'the parameter %s is not an Infile. Cannot rename it\'s file' % self.getName() )
            raise MobyleError , 'Internal Mobyle Error'

    def reset( self ):
        vdef = self.getVdef()
        if vdef is not None:
            convertedVdef , mt = self.convert( vdef , self.getType() )
            if self.getDataType().getName() == 'MultipleChoice':
                sep = self.getSeparator()
                convertedVdef = sep.join( convertedVdef )
            self.getEvaluator().setVar( self.getName() , convertedVdef )
            return convertedVdef
        else:
            self.getEvaluator().setVar( self.getName() , None )
            return None
    
    def getVdef( self ):
        """
        return: the vdef
        @rtype: string or list of string
        """
        return self._vdef


    def setVdef(self, value ):
        """
        set the vdef for this parameter. the vdef is either a value(s) or a code(s).if vdef is a value this one is converted
        @param value: the vdef .
        @type value :is a value, a code or a list of value or a list of code
         - a value = val1
         - a list of value = [val1 , val2, ...] 
        @raise ServiceError: if try to set a vdef and a vdef already exists raise a  L{ServiceError}.
        """
        if self._vdef:
            raise ServiceError, "a vdef is already specify"
        else:
            value_type = type( value )
            if value_type == types.ListType:
                if len( value ) == 1 :
                    self._vdef = value[0]
                else:
                    self._vdef = value
            else:
                self._vdef = value[0]


    def convert( self , value , acceptedMobyleType  ):
        if self._paramfile:
            return self.getDataType().convert( value , acceptedMobyleType , detectedMobyleType = self , paramFile = True )
        else:
            return self.getDataType().convert( value , acceptedMobyleType , detectedMobyleType = self )
        
    def validate(self):
        return self.getDataType().validate( self )
        
    def getType( self ):
        return self._mobyleType
    
    def getDataType( self ) :
        return self._mobyleType.getDataType()
    
    def getBioTypes( self ):
        return self._mobyleType.getBioTypes()
   
    def getAcceptedDataFormats( self ):
        return self._mobyleType.getAcceptedFormats()
    
    def forceReformating( self ):
        return self._mobyleType.forceReformating()
    
    def getDataFormat( self ):
        return self._mobyleType.dataFormat
    
    def setDataFormat( self , format ):
        self._dataFormat = format
    
    def ismaininput(self):
        """
        @return: True if the parameter is mandatory, False otherwise.
        @rtype: boolean
        @call: called by L{Program.ismandatory}
        """
        return self._ismaininput        
         
    def setMaininput(self, value):
        """
        set if this parameter is mandatory or not
        @param value: Boolean
        """
        self._ismaininput = value
 
             
    def ismandatory(self):
        """
        @return: True if the parameter is mandatory, False otherwise.
        @rtype: boolean
        @call: called by L{Program.ismandatory}
        """
        return self._ismandatory        
         
    def setMandatory(self, value):
        """
        set if this parameter is mandatory or not
        @param value: Boolean
        """
        self._ismandatory = value
     
    def ishidden(self ):
        """
        @return: True if this parameter is hidden, False otherwise.
        @rtype: boolean
        @call: called by L{Program.ishidden}
        """
        return self._ishidden
         
         
    def setHidden(self, value):
        """
        set if this parameter is appear in the web interface or not
        @param value: Boolean
        """
        self._ishidden = value
        
    def getArgpos(self):
        """
        """
        if self.iscommand() and not self._argpos :
            return 0
        else:
            return super( Parameter , self ).getArgpos()
        
    def iscommand(self ):
        """
        @return: True if this parameter is the command, False otherwise.
        @rtype: boolean
        @call:  called by L{Program.iscommand}
        """
        return self._iscommand       

    def setCommand(self, value):
        """
        @param value:
        @type value:
        """
        program = self.getProgram()
        if program:
            command = program.getCommand()[0]
            if command:
                msg = "try to set the parmeter \"%s\" as command but the program as already a command" % self.getName()
                s_log.error( msg )
                raise ServiceError , msg
            commandParameterName = program.getCommandParameterName()
            if commandParameterName:
                msg = "try to set parameter \"%s\" as command but the parameter \"%s\" is already set as command" %( self.getName() ,
                                                                                                                      commandParameterName()
                                                                                                                    )
                s_log.error( msg )
                raise ServiceError , msg
        self._iscommand = value
     

    def issimple(self ):
        """
        @return: True if this parameter is simple, False otherwise
        @rtype: boolean
        @call:  called by L{Program.issimple}
        """
        return self._issimple

    def setSimple(self, simple):
        """
        set if the parameter appear in the simple web interface or not
        @param simple:
        @type simple: Boolean
        """
        self._issimple = simple
            
    def isout(self ):
        """
        @return: True if this parameter is produce by the program (an output), False otherwise.
        @rtype: boolean
        @call:  called by L{Program.isout()}
        """
        return self._isout or self._isstdout
        

    def setOut( self , out ):
        """
        defined if the parameter is an output of the program or not
        @param out:
        @type out: boolean
        """
        self._isout = out
        if out :
            self._ishidden = True
            
    def isstdout( self ):
        """
        @return: True if this parameter is produce by the program (an output), False otherwise.
        @rtype: boolean
        @call:  called by L{Program.isstdout()}
        """
        return self._isstdout
        

    def setStdout( self , stdout ):
        """
        defined if the parameter is an output of the program or not
        @param stdout:
        @type stdout: boolean
        """
        self._isstdout = stdout
        self.setOut( stdout )

    def isInfile(self ):
        """
        be careful this method is overriden in the parameter which could be
        Infile ( TextParameter , BinaryParameter ,...)
        @return: False 
        @rtype: boolean
        @call:  called by L{Program.isInfile()}
        """
        dt = self.getDataType()
        if dt.isFile():  
            return not self.isout()
        else:
            return False
        
    def isOutfile(self ):
        """
        be careful this method is overriden in the parameter which could be
        Outfile ( TextParameter , BinaryParameter ,...)
        @return: False 
        @rtype: boolean
        @call:  called by L{Program.isOutfile()}
        """
        dt = self.getDataType()
        if dt.isFile():  
            return  self.isout()
        else:
            return False


    def head( self , data ):
        """
        param data: 
        type data:
        return: return the head of the data 
        rtype:
        """
        return self.getDataType().head( data )

    def cleanData( self , data ):
        """
        param data: 
        type data:
        return: clean data prior to write it on disk
        rtype:
        """
        return self.getDataType().cleanData( data )


    
    def getFormfield(self ):
        """
        @return: the formfield of the parameter if it exist.
        @rtype: string or None
        """
        if self._formfield == "":
            return None
        else:        
            return self._formfield

       
    def setFormfield(self , formfield):
        """
        set the formfield of this parameter
        @param formfield: the formfield
        @type a String representing the formfield
        """
        self._formfield = formfield
        

    def getBioMoby(self ):
        """
        @return: the BioMoby Class corresponding to this parameter
        @rtype:  string or None
        """
        return self._mobyleType.getBioMoby()



    def addElemInVlist (self, label, value):
        """
        add the couple  label,value in a vlist the labels are the keys to retrieve the values
        @param label: the label
        @type label: String
        @param value: the value
        @type value: String
        @raise ValueError: a ValueError if the vlist has already a label label.
        """
        if  self.vlistHas_label( label ):
            raise ValueError , "this label : %s already exist" %label
        else:
            if label:
                label = str( label )
            else:
                label = ''
            if value:
                value = str( value )
            else:
                value = ''
                
            self._vlist[ label ] = value 
            if not hasattr( self._mobyleType , '_vlist' ):
                self._mobyleType._vlist = {}
            self._mobyleType._vlist[ label ] = value

    def delElemInVlist (self,label):
        """
        retrieve the value associated to the label and delete the couple label, value
        @param label: the label
        @type label: String
        @raise UnDefAttrError: a L{UnDefAttrError} if the parameter hasn't any vlist.
        @raise ValueError: a ValueError if the vlist hasn't a label label.
        """
        if not self._vlist:
            raise UnDefAttrError, "no vlist for this Parameter"
        try:
            if not label:
                label = ''
            del self._vlist[label]
            del self._mobyleType._vlist[ label ]
        except KeyError:
            raise  ValueError, " no label %s in this vlist" %label

            
    def getVlist(self ,label):
        """
        @param label: a label in the vlist
        @type label: String
        @return: return the value associated to this label in the vlist
        @rtype: string
        @raise UnDefAttrError: if this parameter haven't vlist raise an L{UnDefAttrError}
        @raise ValueError: if the label doesn't match with any labels in vlist raise a ValueError
        @todo:  revoir le type des erreurs levees
        """
        if not self._vlist:
            raise UnDefAttrError , "this parameter haven't vlist"
        try:
            return self._vlist[label]
        except KeyError:
            raise ValueError , " no label " + str(label)+" in this vlist"

    def vlistLabels(self):
        """
        @return: a list of labels in the vlist
        @rtype: list of string
        """
        return self._vlist.keys()
        

    def hasVlist(self):
        """
        @return: True if the parameter has a vlist, False otherwise.
        @rtype: boolean
        """
        if self._vlist :
            return True
        else :
            return False
        
    def vlistHas_label (self,label):
        """
        @param label: the label to search in vlist
        @type label: String
        @return: True if label match with a label in vlist, false otherwise.
        @rtype:  boolean
        """
        return self._vlist.has_key( label )
    

    def getVlistValues(self):
        """
        @return: a list of all values (not converted) in vlist.
        @rtype: list of string
        @call:  by L{ChoiceParameter} and L{MultipleChoiceParameter}.validate 
        """
        return self._vlist.values()


    def addElemInFlist(self , value , label , codes):
        """
        @param value: 
        @type value: string
        @param label:
        @type label: string
        @param codes:
        @type codes: dictionary
        """
        #print "parameter :" , self.getName()
        #print "addElemInFlist value =", value ," label = ", label ," codes = ",codes
        self._flist[ value ] = ( label , codes )
        if not hasattr( self._mobyleType , '_flist' ):
            self._mobyleType._flist ={}
        else:
            self._mobyleType._flist[ label ] = value
    
    def getFlistValues(self):
        """
        @return: the keys of a flist.
        @rtype: list of strings
        @call: by L{Program}.flistValues
        """
        return  self._flist.keys()


    def flistHas_value(self, value):
        """
        @param value: the value associated to the codes
        @type value: any
        @return: True if the flist has a value == value, False otherwise.
        @rtype: boolean
        @raise UnDefAttrError: if the parameter hasn't flist a  L{UnDefAttrError}
        is raised
        ( called by Parameter.flistProglangs )
        """
        return self._flist.has_key(value)
                           
    def flistLabels(self):
        """
        @return: a list of labels in the flist
        @rtype: list of string
        """
        return self._flist.keys()
 
    def flistProglangs(self, value = None):
        """
        @param value: the value associated to the codes
        @type value: any
        @return: the list of proglang available for a given value.
        @raise UnDefAttrError: if the parameter hasn't flist a  L{UnDefAttrError} is raised
        """
        proglangs = []
        if value is None :
            values = self._flist.keys()
        else:
            if self._flist.flistHas_value( value ):
                values = [ value ]
            else:
                raise MobyleError , "this parameter has no value:" +str( value )+" in it's flist"
        for value in values :
            newValues  = self._flist[ value ][1].keys()
            for newValue in newValues:
                if newValue not in proglangs:
                    proglangs.append( newValue )
        return proglangs
        

    def flistHas_proglang(self,value,proglang):
        """
        @param value: the value associated to the codes
        @type value: any
        @param proglang: the programming language of the code
        @type proglang: String
        @return: Boolean, True if the flist has the value and a code written in proglang associated with, False otherwise.
        @rtype: boolean
        """
        
        if self.flistHas_value(value):
            return self._flist[value][1].has_key( proglang )
        else:
            return False
            #raise ValueError, self.getName()+" : the value " + str(value) + " doesn't exist for this flist"
    
    def getFlistCode(self , value , proglang):
        """
        @param value: the value associated to the codes
        @type value: any
        @param proglang: the programming language of the code
        @type proglang: String
        @return: the code associated with the value and written in proglang.
        @rtype: string
        @raise ParamaterError: if there isn't this value or this proglang an  L{ParamaterError} is raised
        """
        try:
            return self._flist[value][1][proglang]
        except KeyError:
            raise ParameterError, "%s : the proglang %s is not defined for the flist " %( self.getName(),
                                                                                              proglang
                                                                                              )

    def hasFlist(self):
        """
        @return: True if the Parameter has a flist, False otherwise.
        @rtype: boolean
        """
        if self._flist:
            return True
        else:
            return False

    def getListUndefValue( self ):
        """
        @return:
        @rtype: string
        """
        return self._undefValue

    def setListUndefValue(self , value ):
        """
        @param value:
        @type value: string
        """
        self._undefValue = value
        self._mobyleType._undefValue = value
        
    def has_ctrl(self):
        """
        @return: True if the parameter has  L{Ctrl}, False otherwise.
        @rtype:boolean
        """
        if self._ctrls:
            return True
        else :
            return False

    def getCtrls(self):
        """
        @return: the list of Ctrl instances.
        @rtype: list of Ctrl objects.
        @raise UnDefAttrError: if the parameter haven't a Ctrl,  raise an  L{UnDefAttrError}
        """
        if self._ctrls:
            return self._ctrls
        else:
            raise UnDefAttrError,"no ctrl for this parameter"


        
    def addCtrl(self, ctrl):
        """
        @param ctrl: is a tuple made with a list of messages and a list of codes
        @type ctrl: ([(String content , String proglang , String lang , Boolean href)],[(String proglang, String code)])
        """
        myCtrl = Ctrl()
        
        for message in  ctrl[0]:
            if ( (message[1] and message[2]) or (message[1] and message[3]) or (message[2] and message[3]) ):
                raise ServiceError

            if message[1]:
                myCtrl.addMessage(message[0] ,proglang =message[1] )
            elif message[2]:
                myCtrl.addMessage(message[0] ,lang = message[2])
            elif message[3]:
                myCtrl.addMessage(message[0] ,href = message[3] )
                                
        for code in ctrl[1]:
            myCtrl.addCode(code[0] , code[1])

        self._ctrls.append( myCtrl )

    def hasParamfile(self):
        """
        @return: True if the parameter should be specified in a file instead
        the command line, False otehwise
        @rtype: boolean
        """
        if self._paramfile:
            return True
        else:
            return False


    def getParamfile(self):
        """
        @return: the name of the file parameter when they must be specipfied
        in a file instead on command line.
        @rtype: string.
        @raise  UnDefAttrError: if the parameter haven't a paramfile an L{UnDefAttrError} is raised.
        """
        if self._paramfile:
            return self._paramfile
        else:
            raise UnDefAttrError,"no paramfile for this parameter"
        
    def setParamfile(self, fileName):
        """
        set the paramfile
        @param fileName: the name of the paramfile
        @type fileName: String
        """
        #on pourrait des maintenant eliminer les espaces du nom de fichier
        fileName.replace(' ','')
        self._paramfile = fileName

        
    def getFilenames(self, proglang = 'python' ):
        """
        @param proglang: the programming language used to defined the filenames
        @type proglang: string

        @return: the UNIX MASK which permit to retrieve the results files.
        @rtype:  a list of string
        @raise UnDefAttrError:  if the parameter haven't a filenames , raise an  L{UnDefAttrError}
        @call: L{Program.getFileNames}( parameterName )
        @todo:  si ca doit etre evaluer alors il faut considerer ca come du code car la syntaxe va etre differente en perl ,et en python donc je propose de modifier la dtd <!ELEMENT filenames (code)+> et en python maVariable+".*.aln" chaque mask etant separer par un espace
        """
        if not self.isout():
            raise MobyleError, self.getName() + " : only out parameter could have filenames"

        if self._filenames:
            try:
                filenames= self._filenames[ proglang ]
            except KeyError:
                program = self.getProgram()
                if program:
                    programName = program.getName()
                else:
                    programName = "without_program"               
                                
                s_log.warning( "%s.%s have filenames in %s proglangs but not in python" %( programName , self.getName() , self._filenames.keys() ) )
                return []

            #each mask could contain a variable, thus they must be evaluated in evaluator
            result = []
            for mask in filenames:
                try:
                    evaluatedMask = self.getEvaluator().eval( mask )
                    if evaluatedMask is None:
                        # a mask could be a variable therefore it could be None !! 
                        continue 
                    result.append( evaluatedMask )
                except Exception ,err :
                    raise MobyleError, "error in filenames code evaluation ( " + mask + " ) : " + str( err )
            return result
        else:
            raise UnDefAttrError,"no filenames for this parameter"


         
    def setFilenames(self , fileNames , proglang = 'python' ):
        """
        @param fileNames: a unix mask to retrieve the results files (ex: *.aln,*.dnd,...)
        @type fileNames: String
        @param proglang: the programming language used to defined the filenames
        @type proglang: string
        """
        if self._filenames.has_key( proglang ):
            self._filenames[ proglang ].append( fileNames)
        else:
            self._filenames[proglang] = [ fileNames ]
        


    def hasScale( self , proglang = 'python' ):
        """
        @retrun: True if the param has a scale with code in proglang or with value, False otherwise.
        @rtype: boolean
        """
        try:
            _ = self._scalemin[ proglang ]
        except KeyError:
            try:
                _ = self._scalemin['value']
            except KeyError:
                return False
        try:
            _ = self._scalemin[ proglang ]
        except KeyError:
            try:
                _ = self._scalemin[ 'value' ]
            except KeyError:
                return False
        return True

    

    def isInScale( self , proglang = 'python' ):
        """
        @return: True if the value is in range(min, max), false otherwise
        @rtype: boolean
        """
        evaluator = self.getEvaluator()
        try:
            smin = self._scalemin[ proglang ]
        except KeyError:
            try:
                smin = self._scalemin[ 'value' ]
            except KeyError:
                raise MobyleError,  "no value nor code in %s for this scale min" % proglang 
        try:
            smin = evaluator.eval( smin )
        except Exception , err :
            s_log.error( "error during scale min evaluation : %s. Check %s.%s definition" %( err ,
                                                                                             self.getProgram().getName() , 
                                                                                             self.getName()))
            raise MobyleError( "Internal Server Error" ) 
        try:
            smax = self._scalemax[ proglang ]
        except KeyError:
            try:
                smax = self._scalemax[ 'value' ]
            except KeyError:
                raise MobyleError ,"no value nor code in %s for this scale max" % proglang 
        try:
            smax = evaluator.eval( smax )
        except Exception , err :
            s_log.error( "error during scale max evaluation : %s. Check %s.%s definition" %( err,
                                                                                             self.getProgram().getName() , 
                                                                                             self.getName()))
            raise MobyleError( "Internal Server Error" ) 
        value = self.getValue()
        if value is not None:
            
            if value >= smin and value <= smax :
                return True
            else:
                return False
        else:
            raise ValueError , "undefined value" 
        



    def getScale(self , proglang = 'python' ):
        """
        @param proglang: the programming language 
        @type proglang: String

        @return: a tuple ( min , max , inc )
          - min  
          - max 
          - incr is a value
        @rtype: tuple ( , ,  )
        @raise 
        """
        try:
            smin = self._scalemin[ proglang ]
            evaluator = self.getEvaluator()
            min = evaluator.eval( smin )
        except KeyError:
            try:
                smin = self._scalemin[ 'value' ]
            except KeyError:
                raise MobyleError , "no value nor code in %s for this scale min" % proglang 
        try:
            smax = self._scalemin[ proglang ]
            evaluator = self.getEvaluator()
            smax = evaluator.eval( smax )
        except KeyError:
            try:
                smax = self._scalemax[ 'value' ]
            except KeyError:
                raise MobyleError , "no value nor code in %s for this scale max" % proglang
        return ( smin , smax , self._scaleinc )

    

    def setScale(self, min , max , inc = None , proglang = None):
        """
        @param min: specify the minimum of the scale
        @type min: could either a value or String representing a code
        @param max: specify the maximum of the scale
        @type max: could either a value or String representing a code
        @param inc: specify the incrementation of the scale
        @type inc: a number
        @parameter proglang: if min, max are code, proglang should be specified and it's the programming language.
        @type proglang: a String
        @todo: faire des tests sur inc le convertir?
        """
        if proglang:
            self._scalemin[ proglang ] = min
            self._scalemax[ proglang ] = max
        else:
            self._scalemin[ 'value' ] = min
            self._scalemax[ 'value' ] = max
        if inc:
            self._scaleinc= inc
        
        
    def getSeparator( self ):
        """
        @return: a character used to split the values of a MultipleChoice,( default value : '')
        @rtype: string
        """
        return self._separator
        

        
    def setSeparator( self , separator ):
        """
        @param separator: a character used to split the values of a MultipleChoice
        @type separator: String
        """
        self._separator = separator


    def getWidth( self ):
        """
        @return: an Integer, representing the width of the widget.
        @rtype: number
        @raise UnDefAttrError: if the parameter haven't a width , raise an  L{UnDefAttrError}
        """
        if self._width:
            return self._width
        else:
            raise UnDefAttrError,"no width for this parameter"

        
    def setWidth( self , width ):
        """
        @param width: the width of the widget in pixels,en pourcentage ???
        @type width: number int float
        """
        try:
            width + 3
            self._width = width
        except TypeError:
            raise ServiceError , "width must be a number"


    def getHeight(self ):
        """
        @return: return the height of the widget in pixels, en pourcentage????
        @rtype: number
        @raise UnDefAttrError: if the parameter haven't a height , raise an  L{UnDefAttrError}
        """
        if self._height:
            return self._height
        else:
            raise UnDefAttrError,"no height for this parameter"

    

    def setHeight(self, height):
        """
        @param height: the height of the widget in pixels,en pourcentage ???
        @type:number int float??
        """
        try:
            height + 3
            self._height = height 
        except TypeError:
            raise  ValueError, "height must be a number"


    def setExemple(self, value):
        """
        set an exemple value
        @param value: a typical value for this parameter
        @type value: string
        """
        self._exemple = value
        
    def getExemple(self ):
        """
        @return: a typical value for this parameter.
        @rtype: string
        @raise UnDefAttrError: if the parameter haven't an exemple value, raise an L{UnDefAttrError} 
        """
        if self._exemple:
            return self._exemple
        else:
            raise UnDefAttrError,"no exemple for this parameter"


    def doCtrls(self):
        """
        do the controls specific to this parameter        
        @raise  L{UserValueError}: if a control failed a  L{UserValueError} is raised, otherwise return True
        @todo: gerer les message de type href, discuter du proto de la fonction doit retourner False ou lever une erreur??
        @todo: gerer la langue dans la fonction d'erreur
        """
        if self.has_ctrl():
            evaluator = self.getEvaluator()
            myName = self.getName()
            for ctrl in self.getCtrls():
                if ctrl.has_proglang( 'python' ):
                    rawVdef = self.getVdef()
                    if rawVdef is None:
                        evaluator.setVar( 'vdef' , None )
                        convertedVdef = None
                    else:
                        convertedVdef = self.convert( rawVdef , self.getType() )
                        evaluator.setVar( 'vdef' , convertedVdef )
                    if evaluator.getVar( myName ) is not None:
                        value = evaluator.getVar( myName )
                        evaluator.setVar( 'value' , value )
                    else:
                        value = convertedVdef
                        evaluator.setVar( 'value' , convertedVdef )
                    try:
                        code = ctrl.getCode( proglang= 'python' )
                        eval_result = evaluator.eval( code )
                        if self.getDebug() > 1 :
                            b_log.debug( "convertedVdef = " + str(convertedVdef) + "  value = " + str( value) ) 
                            b_log.debug( "eval( " + code + " ) = " + str( eval_result ) )
                    except Exception ,err:
                        msg = self.getName() + ": error during evaluation of \"" + code +"\" : " + str( err )  
                        s_log.error( msg )
                        raise ServiceError , msg
                    if eval_result :
                        continue
                    else:
                        messType = ctrl.whatIsIt()
                        LANG = _cfg.lang()
                        if messType == 'text':
                            if ctrl.messageHas_lang( LANG ):
                                msg = myName +" : "+ ctrl.getMessage( LANG )
                            else:
                                if ctrl.messageLangs():
                                    msg =  myName +" :"+ ctrl.getMessage( ctrl.messageLangs()[0] )
                                else:
                                    msg = "this value"+ str(self.getValue())+" is not allowed for parameter named " + myName
                        elif messType == 'code':
                            if ctrl.messageHas_proglang('python'):
                                msg= myName + " : " + evaluator.eval( ctrl.getMessage( proglang='python' ) )
                            else:
                                msg = "this value" + str( self.getValue() ) + " is not allowed for parameter named " + myName
                        elif messType == 'href':
                            #### TODO ####
                            raise NotImplementedError, "href are not implemented in message Ctrls : todo"
                        else:
                            msg = "this value" + str( self.getValue() ) + " is not allowed for parameter named " + myName
                        #s_log.error( self.getName() + " xml ctrl failed : " + msg )
                        raise UserValueError( parameter = self,  msg = msg )
                else:
                    if self.getDebug() > 1:
                        if ctrl.has_proglang( 'perl' ): 
                            b_log.debug( "############## WARNING #####################" )
                            b_log.debug( "had a control code in Perl but not in Python" )
                            b_log.debug( "############################################" )
        return True

    def _isNumber(self, value):
        """
        test if the value is a number.
        @param value: any value to test
        @type value: any
        @return: True if value is a number, False othewise
        @rtype:  boolean
        """
        try:
            value + 3
            return True
        except TypeError:
            return False


########################
#                      #
#      class text      #
#                      #
########################

class Text(object):
    """
    is used to handle a (text)+ in the mobyle dtd.
    a text in dtd could be either a
     - text
     - code
     - or a href
    and have the attributes
     - lang associated with the text
     - proglang associated with code
     - href for href
    """
    
    def __init__(self):
        self._lang = {}
        self._code = {}
        self._href = []

    def has_lang(self, lang ):
        """
        @param lang: the language in which the text is written
        @type lang: a String should be conformed to the iso630-1 code
        (ex 'en', 'fr').
        @return: True if this Text have a code in this programming language,
        False otherwise
        @rtype: boolean
        """
        if self._lang:
            return self._lang.has_key( lang )
        else:
            return False


    def langs(self):
        """
        @return: the languages of this Text.
        @rtype: list of strings
        """
        return self._lang.keys()

    def addText(self, text, lang ='en'):
        """
        Set a text for this Text
        @param text: the text
        @type text: String
        @param lang: the language in which the text is written
        @type lang: a String should be conformed tothe iso630-1 code
        (ex 'en', 'fr')
        """
        self._lang[ lang ] = text

    def getText(self, lang='en'):
        """
        get the text associatde with the lang for this Text
        @param lang: the language of the text
        @type lang:the language in which the text is written
        @type lang: a String should be conformed tothe iso630-1 code
        (ex 'en', 'fr')
        @return: the text
        @rtype: string
        @raise MobyleError: a{MobyleError} is raised if the text has no lang = 'lang'
        """
        try:
            return  self._lang[lang]
        except KeyError:
            raise MobyleError, "no lang = "+str(lang)+" in this Text"
    


    def has_proglang(self, proglang):
        """
        @param proglang: the programming language ('python', 'perl' ...) 
        @type proglang: string
        @return: True if this Text have a code int his programming language,
        False otherwise.
        @rtype: boolean
        """
        return proglang in self._code

    def proglangs(self):
        """
        @return: a list of string encoding the programming languages of this Text
        @rtype: list of strings
        """
        return self._code.keys()

    def addCode(self, code, proglang='python'):
        """
        Set a code for this Text
        @param code: the code
        @type code: String
        @param proglang: the programming language of the text
        @type proglang: String
        """
        self._code[ proglang ]= code


    def getCode(self,proglang = 'python'):
        """
        Get the code associated with the lang for this Text
        @param proglang: the programming language of the code
        @type proglang:the programming language in which the code is written ('perl, 'python')
        @type proglang: a String 
        @return: the code
        @rtype: string
        @raise MobyleError: a  L{MobyleError} is raised if there isn't any code written in proglang
        """
        try:
            return self._code[ proglang ]
        except KeyError:
            raise MobyleError, "no proglang = "+ str( proglang )+ " in this Text"
        
    def has_code(self , proglang = 'python'):
        if proglang in self._code:
            return bool( self._code[ proglang ] )
        else:
            return False

    def has_href(self):
        """
        @return: True if the Text has a href, False otherwise.
        @rtype: boolean
        """
        if self._href:
            return True
        else:
            return False

    def hrefs(self):
        """
        @return: a list of string encoding  the href.
        @rtype: list of string
        """
        return self._href

    def addHref(self, href):
        """
        set a href for this Text
        @param href: the href it could be a String or a set (liste or tuple) of Strings
        @type href: String
        """
        if type(href) == type([]) or type(href) == type( () ):
            self._href += href
        else:
            self._href.append(href)


    def whatIsIt(self):
        """
        @return: 'text', 'code' if  'href' the Text is a text a code or a href or None if text is empty.
        @rtype: string
        @call: by L{Parameter.doCtrls() <Parameter>}
        """
        if self._lang:
            return 'text'
        elif self._code:
            return 'code'
        elif self._href:
            return 'href'
        else:
            return None

        
    def __str__(self):
        return str(self._lang ) + str(self._code) + str (self._href)
      


######################
#                    #
#     class Ctrl     #
#                    #
######################


class Ctrl(object):
    """
    is used to handle a ctrl in the mobyle dtd.
    a ctrl is a message associated with one or more code 
    """

    def __init__(self):
        self._code = {}
        self._message = Text()

    def getMessage(self, lang = None, proglang= None, href= False):
        """
        @param lang: is the symbol of a lang in iso639-1 (ex: 'en', 'fr') for the text or 'href' for the link
        @type lang: String
        @param proglang: the programming language 
        @type proglang: String
        @param href: if the message is a link toward an external page
        @type href: Boolean
        @return: The message corresponding to the specified lang or proglang or href
        @rtype: string
        @raise MobyleError: if more than one parameter is specified a L{MobyleError} is raised
        """
        if ( (proglang and lang) or (proglang and href) or (lang and href) ):
            raise MobyleError, "invalid argument for getMessage" 
        if proglang:
            return self._message.getCode( proglang)
        elif lang:
            return self._message.getText( lang)
        elif href:
            return self._message.hrefs( )
        else :
            raise MobyleError, "invalid argument for message : "+str(lang)+" , "+str(proglang)+" , "+str(href)

           

    def getCode(self,proglang = 'python'):
        """
        @param proglang: the programming language 
        @type proglang: String
        @return: The code
        @rtype: string
        @raise MobyleError: if there is no code written in proglang raise L{MobyleError}
        """
        try:
            return self._code[proglang]
        except KeyError:
            raise MobyleError, "no code in "+str(proglang)+" for this control"
        
    def proglangs(self):
        """
        @return: the list of programming langage of the code associated to this Ctrl.
        @rtype: list of string
        """
        return self._code.keys()


    def has_proglang(self, proglang = 'python'):
        """
        @param proglang: the programming language
        @type proglang: String
        @return: True if False otherwise.
        @rtype: boolean
        """
        return self._code.has_key(proglang)

    def messageHas_lang(self, lang = 'en'):
        """
        @param lang: the language of the text, according to the iso639-1
        @type lang: String
        @return: True if lang is used to encode the message, False otherwise
        @rtype: boolean
        """
        return self._message.has_lang( lang )

    def messageLangs(self):
        """
        @return: the list of the langs used to encode the message
        @rtype: list of string
        """
        return self._message.langs()
    
    def messageHas_proglang(self, proglang = 'python'):
        """
        @param proglang:
        @type proglang: String
        @return: True if the proglang is used to encode the message, False otherwise
        @rtype: boolean
        """
        return self._message.has_proglang(proglang)
    

    def messageProglangs(self):
        """
        @return: the list of the programming languages to encoding the message
        @rtype: list of string
        """
        return self._message.proglangs()

    def messageHrefs(self):
        """
        @return: the list of href
        @rtype: list of strings
        """
        return self._message.hrefs()
    
    
    def addMessage(self, content ,lang = None, proglang= None, href= False):
        """
        @param content: it must be a text if lang is specified, a code if proglang is specified or a href if href is true 
        @type content: String
        @param lang: the language if the content is a text (2 letters code)
        @type lang: String
        @param proglang: the programming language if the content is a code
        @type proglang: String
        @param href: true if the content is a href
        @type href: Boolean
        """
        if ( (lang and proglang) or (lang and href) or (proglang and href) ):
            raise MobyleError
        else:
            if lang:
                self._message.addText(content,lang=  lang)
            elif proglang:
                self._message.addCode(content, proglang= proglang)
            elif href:
                self._message.addHref(content)

    def whatIsIt(self):
        """
        @return: 'text', 'code' or 'href' if the message is a text a
        code or a href or None if the message is empty.
        @rtype: string
        """
        return self._message.whatIsIt()
    
        
    def addCode(self, code ,proglang ):
        """
        @param proglang:
        @type proglang: String
        @param code:
        @type code: String
        """
        self._code[ proglang ] = code
        
        
        
class flist(object):
    
    def __init__( self ):
            self._flist = {}
    
     
    def addElemInFlist(self , value , label , codes):
        """
        @param value: 
        @type value: string
        @param label:
        @type label: string
        @param codes:
        @type codes: dictionary
        """
        self._flist[ value ] = ( label , codes )
        
    def flistValues(self):
        """
        @return: the keys of a flist.
        @rtype: list of strings
        @call: by L{Program}.flistValues
        """
        return  self._flist.keys()


    def flistHas_value(self, value):
        """
        @param value: the value associated to the codes
        @type value: any
        @return: True if the flist has a value == value, False otherwise.
        @rtype: boolean
        @raise UnDefAttrError: if the parameter hasn't flist a  L{UnDefAttrError}
        is raised
        ( called by Parameter.flistProglangs )
        """
        return self._flist.has_key(value)
                           

    def flistProglangs(self, value):
        """
        @param value: the value associated to the codes
        @type value: any
        @return: the list of proglang available for a given value.
        @raise UnDefAttrError: if the parameter hasn't flist a  L{UnDefAttrError} is raised
        """
        proglangs = []
        for value in self._flist.keys():
            newValues  = self._flist[ value ][1].keys()
            for newValue in newValues:
                if newValue not in proglangs:
                    proglangs.append( newValue )
        return proglangs
        

    def flistHas_proglang(self,value,proglang):
        """
        @param value: the value associated to the codes
        @type value: any
        @param proglang: the programming language of the code
        @type proglang: String
        @return: Boolean, True if the flist has the value and a code written in proglang associated with, False otherwise.
        @rtype: boolean
        """
        if self.flistHas_value(value):
            return self._flist[value][1].has_key( proglang )
        else:
            return False

    
    def getFlistCode(self , value , proglang):
        """
        @param value: the value associated to the codes
        @type value: any
        @param proglang: the programming language of the code
        @type proglang: String
        @return: the code associated with the value and written in proglang.
        @rtype: string
        @raise ParamaterError: if there isn't this value or this proglang an  L{ParamaterError} is raised
        """
        try:
            return self._flist[value][1][proglang]
        except KeyError:
            raise ParameterError, "the proglang %s is not defined for the flist " % proglang
            
class MobyleType(object):
    
    def __init__( self , dataType ,
                  bioTypes = [] , 
                  dataFormat = None , 
                  item_nb = None ,
                  format_program = None ,
                  acceptedFormats = [] , 
                  card = ( 1 , 1 ) , 
                  biomoby = None):
        """
        @param bioType: ADN Protein 
        @type bioType: a list of strings
        @param dataType: Sequence , Structure , ...
        @type dataType:  a DataType instance
        @param format: the real format of the data
        @type format: string
        @param acceptedFormats: the format that are allowed for this data and forceformat. 
         forceformat implied the reformatting of the data either the format match one acceptedFormats.
        @type acceptedFormats: [ ( string format , boolean force ) , ... ]
        @param card: min max. min and max could be an integer or n
        @type card: ( int , int ) or (int , string n) 
        """
        if type( bioTypes ) == types.StringType:
            self.bioTypes = [ bioTypes ]
        else:
            self.bioTypes = bioTypes
        self.dataType = dataType
        if dataFormat is not None and acceptedFormats:
            raise MobyleError( "you cannot set acceptedFormat and format for the same MobyleType object" )
        self.acceptedFormats = acceptedFormats
        self.dataFormat = dataFormat
        self.item_nb = item_nb
        self.format_program = format_program
        if len( card ) != 2:
            raise MobyleError( "the cardinality must be a tuple ( min , max )" )
        self.card = card
        self.biomoby = biomoby
    
    def __str__(self):
        s = 'dataType : '+str( self.dataType ) 
        for attr in ( 'bioTypes' , 'dataFormat' , 'item_nb' , 'format_program' ,
                      'acceptedFormats' , 'card' ,'biomoby' ):
            s =" %s , %s : %s " %( s , attr , getattr( self , attr ) ) 
        return s
    
    def __eq__(self , other ):
        if isinstance( self, other.__class__ ):
            other_acceptedFormats = [ f for f in other.acceptedFormats ]
            other_acceptedFormats.sort()
            self_acceptedFormats = [ f for f in self.acceptedFormats ]
            self_acceptedFormats.sort()
            if other.bioTypes == self.bioTypes \
                and other.dataType == self.dataType \
                and other_acceptedFormats == self_acceptedFormats \
                and other.dataFormat == self.dataFormat \
                and other.card == self.card \
                and other.biomoby == self.biomoby:
                return True
        return False
        
            
    def toDom( self ):
        from lxml import etree        
        typeNode = etree.Element( "type" )
        if self.bioTypes :
            for biotype in self.bioTypes :
                bioTypeNode = etree.Element( "biotype" )
                bioTypeNode.text = biotype 
                typeNode.append( bioTypeNode )
        dataTypeNode = self.dataType.toDom()
        typeNode.append( dataTypeNode )    
        if self.acceptedFormats:
            for format , force in self.acceptedFormats :
                if force:
                    formatNode = etree.Element( "dataFormat" , force = "1")
                else:
                    formatNode = etree.Element( "dataFormat" )
                formatNode.text = format 
                typeNode.append( formatNode )
        elif self.dataFormat:
            formatNode = etree.Element( "dataFormat" )
            formatNode.text = self.dataFormat
            typeNode.append( formatNode )
            #ajouter le format_program et item_nb ?
        if self.card != ( 1 , 1 ):
            min , max = self.card
            cardText= "%s,%s"%( min , max )
            cardNode = etree.Element( "card" )
            cardNode.text =  cardText 
            typeNode.append( cardNode )
        elif self.item_nb :
            cardNode = etree.Element( "card" )
            cardNode.text = str( self.item_nb )
            typeNode.append( cardNode )
        if self.biomoby:
            biomobyNode = etree.Element( "biomoby" )
            biomobyNode.text =  str( self.biomoby ) 
            typeNode.append( biomobyNode )
        return typeNode
    
    def getBioTypes( self ):
        return self.bioTypes
    
    def getDataType( self ):
        return self.dataType
   
    def convert(self , value , acceptedMobyleType , paramFile= False ):
        """
        convert the sequence contain in the file fileName in the rigth format
        throws an UnsupportedFormatError if the output format is not supported
        or a MobyleError if something goes wrong during the conversion.

        @param value: is a tuple ( src , srcFileName) 
          - srcfilename is the name of the file to convert in the src
          - src must be a L{Job} instance the conversion are perform only by jobs (not session) .
        @type value: ( L{Job} instance dest, L{Job} instance, src)
        @return: the fileName ( basename ) of the  sequence file and the effective MobyleType associated to this 
        value
        @rtype: ( string fileName , MobyleType instance )
        @raise UnSupportedFormatError: if the data cannot be converted in any suitable format
        """
        outFileName , converted_mt =  self.dataType.convert(value , acceptedMobyleType , detectedMobyleType = self , paramFile = paramFile)
        if self.bioTypes and converted_mt:
            converted_mt.bioTypes = [ b for b in self.bioTypes ]
        return outFileName , converted_mt
    
    def detect( self , value ):
        """
        detects the format of the sequence(s) contained in fileName
        @param value: the src object and the filename in the src of the data to detect
        @type value: tuple ( session/Job/MobyleJob instance , string filename )
        @return: a tuple of the detection run information:
            - the detected format,
            - the detected items number,
            - program name used for the detection.
        """
        detected_mt = self.dataType.detect( value )
        if self.bioTypes :
            detected_mt.bioTypes = [ b for b in self.bioTypes ]
        if self.dataFormat and not detected_mt.dataFormat: #I trust the format provided by Job ...
            detected_mt.dataFormat = self.dataFormat
        return detected_mt
    
    def getAcceptedFormats( self ):
        return self.acceptedFormats
    
    def setAcceptedFormats( self , acceptedDataFormats ):
        if self.dataFormat:
            raise MobyleError("you cannot set acceptedFormat and format for the same MobyleType object" )
        self.acceptedFormats = acceptedDataFormats
        
    def getDataFormat( self ):
        return self.dataFormat
    
    def setDataFormat(self , format):
        if self.acceptedFormats:
            raise MobyleError("you cannot set acceptedFormat and format for the same MobyleType object" )
        self.dataFormat = format
            
    def getItemNumber( self ):
        return self.item_nb
    
    def setItemNumber( self , nb ):
        self.item_nb = nb
    
    def getFormatProgram( self ):
        return self.format_program 

    def getCard( self ):
        return self.card
    
    def getBioMoby( self ):
        return self.biomoby
    
    def isPipeableTo( self , inputMT ):
        """
        @param inputMT: The "target" input parameter type
        @type inputMT: MobyleType
        @return: True if the data that have this type can be piped to a program input with a MobyleType defined as inputMT
        @rtype: boolean
        """
        if self._isBioTypePipeable( inputMT.getBioTypes() ) and self.dataType.isPipableToDataType( inputMT.getDataType() ) and self._isCardPipeable( inputMT.getCard() ):
            return True
        else:
            return False
        
        
    def _isBioTypePipeable(self , inputBioTypes ):         
        """
        @param inputBioTypes: The "target" input parameter biotype
        @type inputBioTypes: List
        @return: True if the data that have this biotype can be piped to a program input with a biotype defined as inputBioTypes
        @rtype: boolean
        """
        for bioType in inputBioTypes:
            if bioType in self.bioTypes:
                return True
        return False
    
    def _isCardPipeable( self , inputCard ):
        """
        @param inputCard: The "target" input parameter cardinality
        @type inputCard: tuple
        @return: True if the data that have this cardinality can be piped to a program input with a cardinality defined as inputCard
        @rtype: boolean
        """
        inputMin , inputMax = inputCard
        if  inputMax == 'n':
                return True
        else:
            if type( self.card[1] ) == types.IntType and inputMax < self.card[1]: 
                return True
        return False
        
        
    def isFile(self):
        """
        @return: True if the datatype corespond to a file , false otherwise
        @rtype: boolean
        """
        return self.dataType.isFile()
                
    def toFile(self , data  , dest , destFileName , src , srcFileName ):
        if self.dataType.isFile():
            return self.dataType.toFile( data  , dest , destFileName , src , srcFileName )
        else:
            raise MobyleError( "this data is not a file" )
