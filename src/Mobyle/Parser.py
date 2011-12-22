########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

"""
 Tools to parse and build services for Mobyle

"""
import os.path
from lxml import etree
from logging import getLogger
b_log = getLogger( 'Mobyle.builder' )
p_log = getLogger( __name__ )

import Mobyle.Service
from Mobyle.Classes.DataType import DataTypeFactory
from Mobyle.Evaluation import Evaluation

from Mobyle.MobyleError import MobyleError , ParserError
from Mobyle.ConfigManager import Config

__extra_epydoc_fields__ = [('call', 'Called by','Called by')]



def parseService( serviceUrl  , debug = 0 ) :
    """
    @param serviceUrl: the url of a Mobyle Service definition
    @type serviceUrl: string
    @return: a service
    @rtype: service instance
    """
    try:
        servicePath = serviceUrl
    except KeyError:
        raise MobyleError , "the service %s doesn't exist" % serviceUrl
    
    parser = etree.XMLParser( no_network = False )
    doc = etree.parse( servicePath , parser )
    root = doc.getroot()
    if root.tag == "program":
        service = parseProgram( root , debug = debug )
    elif root.tag == "workflow":
        service = parseWorkflow( root )
    else:
        raise ParserError , "a service must be a program or a workflow"
    service.header.setUrl( serviceUrl )   
    return service

    
    
def parseWorkflow( workflowNode ):
        raise NotImplementedError, "parsePipeline is not yet implemented todo"

    
    
    
def parseProgram( programNode , debug = 0 ):
    ######################################
    #
    #  validation 
    #
    ######################################
    evaluator = Evaluation() 
    dataTypeFactory = DataTypeFactory()
    program = Mobyle.Service.Program( evaluator )
    headNode = programNode.find( "./head" )
    header = parseHeader( program , headNode , context = program )
    program.addheader( header )
    allParameterNodes = programNode.findall( './parameters/parameter[name]')
    for parameterNode in allParameterNodes:
        try:
            program.addParameter( parseParameter( parameterNode , 
                                                  evaluator = evaluator, 
                                                  dataTypeFactory = dataTypeFactory,
                                                  context = program ) )
        except MobyleError , err :
            raise ParserError , "%s : %s : %s" %( program.getName() ,
                                                  parameterNode.find( "./name" ).text ,
                                                  err
                                                  )
    allParagraphNodes = programNode.findall( './parameters/paragraph')
    for paragraphNode in allParagraphNodes:
        program.addParagraph( parseParagraph( paragraphNode , 
                                              evaluator = evaluator, 
                                              dataTypeFactory = dataTypeFactory, 
                                              context = program )  )
    if debug > 1:
        b_log.debug("""
        \t##########################################
        \t#                                        #
        \t#              vdefs filling             #
        \t#                                        #
        \t##########################################
        """)
    #service.resetAllParam() #tous les parametres sont dans l'evaluateur
    for paramName in program.getAllParameterNameByArgpos() :
        #all parameters must be in evaluation space
        #in some output parameters there is a format element eg to rename the output file
        # see outfile parameter in protdist.xml ( this renaming is mandatory to avoid conflict 
        # when 2 phylip job are piped
        try:
            program.reset( paramName )
        except MobyleError , err :
            msg = "%s.%s : invalid vdef : %s" %( program.getName(),
                                             paramName ,
                                             err
                                             )
            if debug < 2 :
                p_log.critical( msg )
            else:
                p_log.error( msg )
            raise MobyleError , msg
    return program
    

def parseHeader( service ,  headNode , context = None ):
    """
    fill the head of the service with thw element from the headNode
    @param service: the service
    @type service: a Program instance or WorkflowDef instance
    @param headNode: a node representing a header
    @type headNode: a dom object 
    """
    header = Mobyle.Service.Header()
    name = headNode.find( "name" ).text
    header.setName( name )
    try:
        version = headNode.find( "version" ).text
        header.setVersion( version )
    except AttributeError:
        pass
    title = headNode.find( "doc/title" ).text
    header.setTitle( title )
    doclinks = headNode.findall( "doc/doclink" )
    for doclink in doclinks:
        header.addDoclink( doclink.text )
    categoryNodes = headNode.findall( "category" )
    categories = []
    for categoryNode in categoryNodes:
        categories.append( categoryNode.text )
    if categories:
        header.addCategories( categories )
    try:
        commandNode = headNode.find( "command" )
        command = commandNode.text
        type = commandNode.get( "type" )
        path = commandNode.get( "path" )
        if type and path:
            header.setCommand( command , type = type , path = path )
        elif type:
            header.setCommand( command , type = type )
        elif path:
            header.setCommand( command , path = path )
        else:
            header.setCommand( command )
    except AttributeError:
        pass
    envNodes = headNode.findall( "env" )
    for envNode in envNodes:
        try:
            envName = envNode.get( 'name')
            envValue = envNode.text
            header.addEnv( envName , envValue )
        except IndexError:
            raise ParserError , "invalid env element in head"
    return header  


def parseParagraph( paragraphNode , evaluator  = None , dataTypeFactory = None , context = None):
    paragraph = Mobyle.Service.Paragraph( evaluator )
    if dataTypeFactory is None:
        dataTypeFactory = DataTypeFactory()
    name = paragraphNode.find( "name" ).text
    paragraph.setName( name )
    for promptNode in paragraphNode.findall( './prompt' ): # plusieurs prompts dans des lang differents
        promptLang = promptNode.get( 'lang' )
        if promptLang is None:
            prompt = promptNode.text
            prompt = prompt.strip()
            if prompt:
                paragraph.addPrompt( prompt )
            else:
                continue #the element prompt is empty
        else:
            prompt = promptNode.text
            prompt = prompt.strip()
            if prompt:
                paragraph.addPrompt( prompt , lang = promptLang )
            else:
                continue #the element prompt is empty
    precondNodes = paragraphNode.findall( './precond/code' )
    for precondNode in precondNodes :
        precond = precondNode.text
        proglang = precondNode.get( 'proglang' )
        if proglang :
            paragraph.addPrecond( precond , proglang = proglang )
        else:
            paragraph.addPrecond( precond )
    try:
        argpos = paragraphNode.find( './argpos' ).text
        paragraph.setArgpos( int( argpos ) )
    except AttributeError:
        pass
    except ValueError:
        raise ParserError , "Argpos must be an integer"
    
    format = paragraphNode.find( './format' ) 
    if format :
        for codeNode in format.find( './code'):
            proglang = codeNode.get( 'proglang' )
            code = codeNode.text
            paragraph.addFormat( code , proglang)
    
    ##################################
    #
    #   descente recursive dans l'arbre des paragraphes et paramettres
    #
    ##################################
    paragraphChildNodes = paragraphNode.findall( './parameters/paragraph')
    for paragraphChildNode in paragraphChildNodes:
        paragraphChild = parseParagraph( paragraphChildNode , 
                                         evaluator = evaluator , 
                                         dataTypeFactory = dataTypeFactory ,
                                         context = context )
        paragraph.addParagraph( paragraphChild )
    parameterChildNodes = paragraphNode.findall( './parameters/parameter')
    for parameterChildNode in parameterChildNodes:
        try:
            parameterChild = parseParameter( parameterChildNode , 
                                             evaluator = evaluator, 
                                             dataTypeFactory = dataTypeFactory,
                                             context = context )
        except MobyleError , err :
            raise ParserError , "error while parsing parameter %s : %s" %( parameterChildNode.find( "./name").text ,
                                                  err
                                                  )
        paragraph.addParameter( parameterChild )
    return paragraph 

    

def parseParameter( parameterNode , evaluator = None , dataTypeFactory = None , context = None):
    attrs = parameterNode.attrib
    try: 
        out = attrs.get( 'isout' , None ) == "1" or  attrs.get( 'isstdout' , None ) == "1" 
        typeNode = parameterNode.find( "./type")
        mobyleType = parseType(  typeNode , 
                                 dataTypeFactory = dataTypeFactory , 
                                 out = out ,
                                 context = context
                                )
    except ( ParserError , MobyleError ), err :
        raise ParserError , "error while parsing parameter %s : %s" %( parameterNode.find( "./name").text ,
                                              err
                                              )

    parameter = Mobyle.Service.Parameter( mobyleType )
    
    #############################
    #                           #
    #   parsing des attributs   #
    #                           #
    #############################
    
    if 'ismandatory' in attrs and  attrs[ 'ismandatory' ] == "1":
        parameter.setMandatory( True )
    if 'ismaininput' in attrs and  attrs[ 'ismaininput' ] == "1":
        parameter.setMaininput( True )
    if 'iscommand' in attrs and  attrs[ 'iscommand' ] == "1":
        parameter.setCommand( True )
    if 'ishidden' in attrs and  attrs[ 'ishidden' ] == "1":
        parameter.setHidden( True )
    if 'issimple' in attrs and  attrs[ 'issimple' ] == "1":  
        parameter.setSimple( True )
    if 'isout' in attrs and  attrs[ 'isout' ] == "1":
        parameter.setOut( True )
    if 'isstdout' in attrs and  attrs[ 'isstdout' ] == "1": 
        parameter.setStdout( True )
        parameter.setOut( True )
    if 'bioMoby' in attrs and  attrs[ 'bioMoby' ] == "1":    
        parameter.setBioMoby( attrs[ 'bioMoby' ] )
    try:
        name = parameterNode.find( "name" ).text
        parameter.setName( name )
    except AttributeError:
        raise ParserError , "parameter has no tag \"name\""
    
    for promptNode in parameterNode.findall( './prompt' ): # plusieurs prompts dans des lang differents
        promptLang = promptNode.get( 'lang' )
        if promptLang is None:
            parameter.addPrompt( promptNode.text )
        else:
            parameter.addPrompt( promptNode.text , lang = promptLang )
    format = parameterNode.find( './format' ) 
    if format is not None:
        for codeNode in format.findall( './code'):
            proglang = codeNode.get( 'proglang' )
            code = codeNode.text
            if code is None:
                code = "" 
                pname = codeNode.find( "/program/head/name" ).text
                p_log.warning( "find empty element code in %s.%s parameter. The code value is set to \"\" " %( pname , name )  )
            parameter.addFormat( code , proglang)
    
    vdefs = [] # #dans clustalW hgapresidue est un MultipleChoice et la vdef est une liste de valeurs
    for vdefNode in parameterNode.findall( './vdef/value' ):
        vdefs.append( vdefNode.text )
    if vdefs:
        parameter.setVdef( vdefs )
    #the vdef can't be code anymore the service and apidoc must be updated
    #getVdef could return always list 
    try:
        argpos = parameterNode.find( './argpos' ).text
        parameter.setArgpos( int( argpos ) )
    except AttributeError:
        pass
    except ValueError:
        raise ParserError , "Argpos must be an integer"
 
    vlist = parameterNode.find( './vlist' )
    if vlist is not None:
        elems  = vlist.findall('./velem')
        for elem in elems:
            try:
                label = elem.find('./label' ).text
            except AttributeError:
                label = "" 
            try:  
                value = elem.find('./value' ).text
            except AttributeError:
                value = ""
            undef = elem.get( 'undef' )
            if bool( undef ):
                parameter.setListUndefValue( value )
            else:    
                parameter.addElemInVlist(  label , value ) 
        
    flist = parameterNode.find( './flist' )      
    if flist is not None:
        elems  = flist.findall('./felem')
        for elem in elems:
            try:
                label = elem.find( './label' ).text 
            except AttributeError:
                label = ""
            try:
                value = elem.find( './value' ).text
            except AttributeError:
                value = ""
            codes = {}
            for codeNode in elem.findall( './code' ):
                code = codeNode.text
                if code is None:
                    code = "" 
                    pname = codeNode.find( "/program/head/name" ).text
                    p_log.warning( "find empty felem code in %s.%s parameter. The code value is set to \"\" " %( pname , name )  )
                proglang = codeNode.get( 'proglang' )
                if proglang is None:
                    pname = codeNode.find( "/program/head/name").text
                    msg = "find felem code in %s.%s parameter without proglang"%( pname , name ) 
                    p_log.critical(msg)
                    raise ParserError , msg
                codes [ proglang ] = code
            undef = elem.get( 'undef' )
            if bool( undef ):
                parameter.setListUndefValue( value )
            else:                   
                parameter.addElemInFlist( value, label , codes )
            
    ctrls = parameterNode.findall( './ctrl' )
    for ctrl in ctrls:
        messages = []
        codes = []
        messageNodes = ctrl.findall( './message/text' )
        for messageNode in messageNodes:
            message = toText( messageNode)
            messages.append( message )
        for codeNode in ctrl.findall( './code'):
            code = codeNode.text
            proglang = codeNode.get( 'proglang' )
            codes.append( ( code , proglang ) )
        parameter.addCtrl( ( messages , codes ) ) 
   
    precondNodes = parameterNode.findall( './precond/code' )
    for precondNode in precondNodes :
        precond = precondNode.text.strip() 
        if precond == '':
            pname = codeNode.find( "/program/head/name" ).text
            msg = "WARNING: %s/%s: the code of precond is empty" %( pname , name ) 
            b_log.warning( msg ) 
            p_log.warning( msg )
            continue          
        proglang = precondNode.get( 'proglang' )
        if proglang is not None:
            parameter.addPrecond( precond , proglang = proglang )
        else:
            parameter.addPrecond( precond )
    paramfile= parameterNode.find( './paramfile' )
    if paramfile is not None:
        paramfile = paramfile.text
        parameter.setParamfile( paramfile )
    filenamesNode = parameterNode.find( './filenames' )
    if filenamesNode is not None:
        for codeNode in filenamesNode.findall( './code' ):
            parameter.setFilenames( codeNode.text , codeNode.get( 'proglang' ) )
   
    scaleNode = parameterNode.find( './scale')
    if scaleNode is not None:
        minNode = scaleNode.find('./min' )
        maxNode = scaleNode.find('./max' )
        if minNode is None or maxNode is None:
            raise MobyleError, "parameter named:\"%s\" have a malformed element scale" % parameter.getName()
        try:
            inc = scaleNode.find('./inc' ).text
        except AttributeError:
            inc = None
        try:
            max = maxNode.find( './value' ).text
            maxProglang = None
            min = minNode.find( './value' ).text
            minProgLang = None
            parameter.setScale( min , max , inc = inc )
        except AttributeError:
            try:
                minCodes = {}
                maxCodes = {}
                maxCodeNodes = maxNode.findall( './code' )
                minCodeNodes = minNode.findall( './code' )
                for codeNode in maxCodeNodes:
                    maxProglang = codeNode.get( 'proglang' )                    
                    maxCode = codeNode.text
                    maxCodes[ maxProglang ] = maxCode
                for codeNode in minCodeNodes:
                    minProglang = codeNode.get( 'proglang' )                    
                    minCode = codeNode.text
                    minCodes[ minProgLang ] = minCode
                for minProglang in minCodes.keys():
                    parameter.setScale( minCodes[ minProglang ] , maxCodes[ minProglang ] , inc = inc , proglang = minProglang )
            except ( AttributeError , KeyError ) :
                raise ParserError, "parameter named:\"%s\" have a malformed element scale" % parameter.getName()
    separator = parameterNode.find( './separator' )
    if separator is not None:
        if separator.text is None:
            parameter.setSeparator( '' )
        else:
            parameter.setSeparator( separator.text )
    return parameter


def parseType( typeNode , dataTypeFactory = None , out = False , context = None):
    if not dataTypeFactory:
        dataTypeFactory = DataTypeFactory()
    try:
        bioTypes = typeNode.findall( "./biotype" )
        bioTypes = [ bt.text for bt in bioTypes ]
    except IndexError :
        bioTypes = None
    try:    
        card = typeNode.find( "./type/card" ).text
        try:
            min , max = card.split(",")
        except ValueError:
            if len( card ) == 2:
                min = max = card 
            else:
                raise ParserError , "invalid card: %s .the card element must be a string of 2 integer or \"n\" separate by a comma : "% card 
        try:
            min = int( min )
        except ValueError :
            if min != "n":
                raise ParserError , "invalid card: %s .the card element must be a string of 2 integer or \"n\" separate by a comma : "% card 
        try:
            max = int( max )
        except ValueError :
            if max != "n":
                raise ParserError , "invalid card: %s .the card element must be a string of 2 integer or \"n\" separate by a comma : "% card 
        card = ( min , max )
    except AttributeError :
        card = ( 1 , 1 )
    try:
        superKlass = typeNode.find( "./datatype/superclass" ).text
    except AttributeError:
        superKlass = None
    try:
        klass = typeNode.find( "./datatype/class" ).text
    except AttributeError:
        if superKlass is None :
            raise ParserError , typeNode.find( "./name" ).text + " must have either a \"class\" element either a \"class\" and \"superclass\" element"
        else:
            raise ParserError , typeNode.find( "./name" ).text +" if the \"superclass\" is specified the the \"class\" element must be also specified"
    try:
        if superKlass:
            dataType = dataTypeFactory.newDataType( superKlass , xmlName = klass )
        else:
            dataType = dataTypeFactory.newDataType( klass )
    except MobyleError , err :
        raise ParserError , err
    mobyleType = Mobyle.Service.MobyleType( dataType , 
                                            bioTypes = bioTypes , 
                                            card = card )
    
    formatNodes = typeNode.findall( "dataFormat" )
    if not out and context and isinstance( context , Mobyle.Service.Program ):
        acceptedformats = []
        for formatNode in formatNodes :
            format = formatNode.text
            force = formatNode.get( "force" , False ) == '1'
            acceptedformats.append( (formatNode.text , force ) )
        mobyleType.setAcceptedFormats( acceptedformats )
                   
    elif formatNodes:
        dataFormat = formatNodes[0]
        #le format_prg
        mobyleType.setDataFormat( dataFormat.text )
    return  mobyleType  



def toText( textNode ):
    try:
        content = textNode.text.strip()
    except AttributeError:
        content = None
    lang = textNode.get( 'lang' )
    if lang:
        return ( content , None , lang , None )
    
    href = textNode.get( 'href' )
    proglang = textNode.get( 'proglang' )        
    if href is not None:
        return ( content , None , None , href )
    elif proglang is not None:
        return ( content , proglang , None , None )
    else:
        return ( content , None , 'en' , None )

    
