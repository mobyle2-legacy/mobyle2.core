########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.        #
#                                                                                      #
########################################################################################

""" 
Build the command from the parameters chosen by the users
"""

import os
from StringIO import StringIO

from Mobyle.MobyleError import MobyleError
from logging import getLogger
c_log = getLogger(__name__)
b_log = getLogger( 'Mobyle.builder' )
from Mobyle.ConfigManager import Config
_cfg = Config()

__extra_epydoc_fields__ = [( 'call', 'Called by','Called by' )]





class CommandBuilder:
    """
    This class create the command from the parameters chosen by the users
    3 main methods exist
      - buildLocalCommand: to build a unix command line for a local job
      - buildCGI : to build the url, to invoke a cgi
      - buildWS : to build the ,to call a WebService
     """

    def __init__( self , job_dir = None ):
        self._commandLine = "" 
        self._paramfileHandles = {} # the key is the filename,
                                    # the value is the StrinIO file object like
        
    def buildLocalCommand( self, service ):
        """
        Build a unix command line from a - L{Service} instance
        @param service: the service  which correspond to the programm asked by the user
        @type service: a - L{Service} instance
        @return: a String representing the command line
        """
        debug = _cfg.debug( service.getName() )
        commandIsInserted = False
        commandParameterName = service.getCommandParameterName()
        if commandParameterName:
            commandPos = service.getArgpos( commandParameterName )
        else:
            commandPos = 0

        if debug > 1:
            b_log.debug( """\n
            \t#####################################################
            \t#                                                   # 
            \t#               command line building               #
            \t#                                                   #
            \t#####################################################
            \n""" )
            
        myEvaluator = service.getEvaluator()
            
        for parameter in service.getAllParameterByArgpos():
            paramName = parameter.getName()
            if debug > 1:
                b_log.debug( "--------------- " + paramName + " ---------------")
                b_log.debug( "commandIsInserted " + str( commandIsInserted ) )
                b_log.debug( "service.getArgpos( paramName ) " + str( parameter.getArgpos()))
            if not commandIsInserted and parameter.getArgpos() >= commandPos:
                if parameter.iscommand():
                    #the command from parameter is priority vs command
                    #the command comes from this parameter
                    if debug > 1 :
                        b_log.debug( "self._commandLine service.iscommand " + self._commandLine )                            
                    commandIsInserted = True
                else:
                    #I insert the command from command tag in commandLine
                    if debug > 1:
                        b_log.debug( "self._commandLine = " + self._commandLine )

                    self._commandLine += " " + service.getCommand()[0]
                    commandIsInserted = True
                    if debug > 1:
                        b_log.debug( "self._commandLine+ command = " + self._commandLine )
                    
            #set "vdef" and "value" in the protected namespace (evaluator) 
            rawVdef = parameter.getVdef()
            
            if rawVdef is None:
                myEvaluator.setVar( 'vdef' , None )
                convertedVdef = None #TODO a suprimmer qund b_log renove
            else:
                convertedVdef , mt = parameter.convert(rawVdef , parameter.getType() )
                myEvaluator.setVar( 'vdef' , convertedVdef )
                                    
            if debug > 1:
                b_log.debug( "rawVdef = " + str( rawVdef ) )
                b_log.debug( "convertedVdef = " + str( convertedVdef ) )
                b_log.debug( "myEvaluator.setVar( 'vdef' , "+ str( convertedVdef ) +" )")

            if ( myEvaluator.isDefined( paramName ) ) :
                # be careful we can't use the test: if servive.getValue(),
                # because, the value could be fill with False.
                # thus we must test if the value exist or not, and not test the value itself!
                myEvaluator.setVar( 'value', parameter.getValue( ) )
                if debug > 1:
                    b_log.debug( "myEvaluator.isDefined( " + paramName + " ) = True" )
                    b_log.debug( "myEvaluator.setVar( 'value' ,"+ str( parameter.getValue() ) + " )" )
            else:
                myEvaluator.setVar( 'value' , convertedVdef )
                
                if debug > 1:
                    b_log.debug( "myEvaluator.isDefined( " + paramName + " ) = False" )
                    b_log.debug( "rawVdef = " + str( rawVdef ) )
                    b_log.debug( "convertedVdef = " + str( convertedVdef ) ) 
                    b_log.debug( "myEvaluator.setVar( 'value' , " + str( convertedVdef ) + " )" ) 

            if parameter.precondHas_proglang( 'python' ):
                if debug > 1:
                    b_log.debug("precondHas_proglang( "+ paramName +" , 'python' ) = True")
                allPrecondTrue = True
                preconds = parameter.getPreconds( proglang='python' )
                
                for precond in preconds:
                    if not  myEvaluator.eval( precond ):
                        if debug > 1:
                            b_log.debug("eval( "+ precond  +" ) = False")
                        
                        allPrecondTrue = False
                        break
                    else:
                        if debug > 1:
                            b_log.debug("eval( "+ precond  +" ) = True")
                if not allPrecondTrue :
                    continue #next parameter
                
            if parameter.formatHas_proglang( 'python' ):
                if debug > 1:
                    b_log.debug("service.formatHas_proglang( "+ paramName +" , 'python' ) = True")
                format =  parameter.getFormat( 'python' )

            else:
                value = myEvaluator.getVar( 'value' )
                if value is not None :
                    if parameter.flistHas_proglang( value , 'python' ) :

                        if debug > 1:
                            b_log.debug("service.flistHas_proglang( "+ paramName +" , "+ str( value ) + " , 'python' ) = True")

                        format = parameter.getFlistCode( value , 'python' )
                    else:
                        format = None
                else:
                    format = None

            if debug > 1:
                b_log.debug( "value = " + str( myEvaluator.getVar( 'value' )) + "  type = "+ str(type( myEvaluator.getVar( 'value' ) ) ) )
                b_log.debug( "vdef = " + str( myEvaluator.getVar( 'vdef' )) + "  type = "+ str(type( myEvaluator.getVar( 'value' ) ) )   )
                b_log.debug(" format = " + str( format ) )
                
            if format :
                if parameter.hasParamfile():
                    #the Parameter.setParamfile method had already trim the spaces
                    paramfileName = parameter.getParamfile()
                    if paramfileName:
                        if self._paramfileHandles.has_key( paramfileName ):
                            paramfileHandle = self._paramfileHandles[ paramfileName ]
                        else:
                            try:
                                paramfileHandle = self.openParamFile( paramfileName )
                                self._paramfileHandles[paramfileName] = paramfileHandle
                            except IOError:
                                raise MobyleError, "cannot open the file: "+str( paramfileName )
                else :
                    paramfileHandle = None
            else:
                if  myEvaluator.getVar( 'value' ) is not None:
                    if parameter.formatHas_proglang( 'perl' ) or  parameter.flistHas_proglang( parameter.getValue() , 'perl' ) :
                        if debug > 1:
                            b_log.debug( "#################### WARNING ##############################################" )
                            b_log.debug( "the parameter " + paramName + " had a format code in Perl but not in Python" )
                            b_log.debug( "###########################################################################" )
                continue
                
            try:
                arg = myEvaluator.eval( format )
            except Exception, err:
                msg = "Error during evaluation of \"%s.%s\" format parameter: %s : \"%s\"" % (
                    service.getName(),
                    paramName ,
                    format,
                    err
                    )
                if debug > 1:
                    b_log.debug( msg )
                raise MobyleError , msg
                
            if paramfileHandle:
                if debug > 1:
                    b_log.debug( ">> " + paramfileName + " , " + arg )
                if arg :
                    paramfileHandle.write( arg )
                    paramfileHandle.flush()
            else:
                self._commandLine = str( self._commandLine ) + str( arg )
                if debug > 1:
                    b_log.debug( "commandLine = " + self._commandLine )
        if debug > 1:
            b_log.debug( "------------ end of parameter loop  -------------" )        
       
#===============================================================================
#            
#        the environment is modified here ( it will be just before to do run in _batch ) to avoid 
#        dramatic side effects on well of mobyle.
#        we usr the environment to find the right python everywhere in mobyle and if we modified the path
#        we could change the python used.
#                 
#===============================================================================
        xmlEnv = {}
        
        if commandParameterName : #the command come from a parameter
            path  = service.getEnv( 'PATH' )            
        else:#the command come from the element command in head
            path = service.getCommand()[2]
            path_env = service.getEnv( 'PATH' )
            if path and path_env:
                path = "%s:%s" % ( path, path_env )
            elif path_env:
                path = path_env
        if path :
            #os.environ['PATH'] = "%s:%s" %( path , os.environ['PATH'])
            xmlEnv[ 'PATH' ] = path
            if debug > 1:
                b_log.debug( "PATH= " + str( path  ) )            
        else:
            if debug > 1 :
                b_log.debug( "PATH= "+ str( os.environ[ 'PATH' ] ) )
        for varEnv in service.envVars():
            envArg = service.getEnv( varEnv ).strip()
            if varEnv == 'PATH':
                continue
            else:
                xmlEnv[ varEnv ] = envArg
            
        #trim multi espaces , ...
        self._commandLine = ' '.join( self._commandLine.split() )
        self._commandLine.strip()
        self._commandLine.replace( '"','\\"' )
        self._commandLine.replace( '@','\@' )
        self._commandLine.replace( '_SQ_',"\'" )
        self._commandLine.replace( '_DQ_','\"' )


        if debug > 1:
            b_log.debug( "command line= " + self._commandLine )
        return { 'cmd' : self._commandLine , 
                 'env'  : xmlEnv ,
                 'paramfiles': self._paramfileHandles
                }
        

    def __str__( self ):
        return str( self._commandLine )

    def openParamFile(self , paramfileName ):
        return StringIO()
       

