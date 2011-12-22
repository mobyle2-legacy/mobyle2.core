########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.        #
#                                                                                      #
########################################################################################

"""
manage the information in the index.xml
"""
import os
from lxml import etree

from time import localtime, strftime , strptime
import urllib2 , urlparse
import re
import types
import copy

from logging import getLogger
js_log = getLogger( __name__ )

from Mobyle.MobyleError import MobyleError , URLError , HTTPError , JobError
from Mobyle.ConfigManager import Config
_cfg = Config()
from Mobyle.Utils import indent as utils_indent
from Mobyle.Service import Program
from Mobyle.Workflow import Workflow


_extra_epydoc_fields__ = [('call', 'Called by','Called by')]



"""
G{classtree _abstractState , JobState , ProgramJobState , WorkflowJobState }
"""



def path2url( Dir ):
    """
    translate a directory absolute path in mobyle tree into an url in Mobyle 
    @param Dir: the directory to translate this dir should be in Mobyle tree. Doesn't check if the path exist
    @type Dir: string
    @return: an url http corresponding to the directory dir
    @rtype: string
    @raise MobyleError: -L{MobyleError}
    """
    tmpdir = os.path.normpath( _cfg.results_path() ) #remove the ending slash
    begin = Dir.find(tmpdir )
    if begin != -1:
        end = begin + len( tmpdir )
        return "%s/%s" %( _cfg.results_url() , Dir[end:].lstrip( os.path.sep ) )         
    else:
        msg = str( Dir ) + " is not Mobyle directory compliant "
        js_log.error( msg )
        raise MobyleError , msg
    

def url2path( url ):
    jobsUrl = _cfg.results_url()
    if not jobsUrl in url:
        msg =  "url2path: " + str( url ) + " is not a local Mobyle url"
        js_log.warning( msg )
        raise MobyleError, msg
    
    match = re.search( jobsUrl , url )
    begin , end = match.span()
    extrapath = url[ end : ].lstrip( '/' )
    return os.path.normpath( os.path.join( _cfg.results_path() , extrapath ))
    
    
def normUri( uri ):
    """
    normalize the uri
      - if the uri is a distant url , return the url of the directory containing the index.xml
      - if the uri is an local url , return the absolute path
      - if the uri is a local path , return the absolute path
    @param uri:
    @type uri: string
    @return: a normalize uri
    @rtype: string
    @raise: MobyleError if the uri is not a path or uri protocol is not http or file
    """
    protocol ,host, path, _ , _ , _ = urlparse.urlparse( uri )
    
    if protocol == 'file' or protocol == '':
        path = os.path.abspath( os.path.join( host , path ) )        
    elif protocol == 'http':
        root_url =  _cfg.root_url()[7:] #remove the protocol http://
        if host == root_url:
            try:
                path = url2path( uri )
            except MobyleError:
                path = uri
        else:            
            path = uri
    else:
        raise MobyleError, "Mobyle doesn't support this protocol: " + str( protocol )

    if path[-10:] == "index.xml":
        path = path[ : -10 ]
    return path.rstrip( '/' )


def getContentFile( uri ):
    """
    @param uri: the url or a path (absolute or relative) to a file
    @type uri: string
    @return: the content of the file designing by uri as a string
    @rtype: string
    @raise: MobyleError , if the protocol is not supported
    """
    protocol , host , path , _,_,_ = urlparse.urlparse( uri )
    if protocol == '' or protocol == 'file':
        if not os.path.isabs( path ):
            if protocol == 'file':
                path = os.path.abspath( os.path.join( host,path ))
            else:
                path = os.path.abspath( path )
        try:
            fh = open( path , 'r' )
        except IOError, err:
            msg = "getContentFile : " + str( err )
            #js_log.error( msg ) # normal la premiere fois ne plus logger
            raise MobyleError ,err
        
    elif protocol == 'http':
        #urlopen manage HTTP redirect
        try:
            fh = urllib2.urlopen( uri )
        except urllib2.HTTPError, err: #a subclass of URLError
            msg = "unable to get %s : %s" %( uri , err )
            js_log.error( msg )     
            raise HTTPError( err )
        except urllib2.URLError, err:
            msg = "unable to get %s : %s" %( uri , err )
            js_log.error( msg )
            raise URLError( err )
    else:
        raise MobyleError, "Mobyle doesn't support " + protocol + " protocol"
    content = ''
    l = fh.readline()
    while l:
        content = content + l
        l = fh.readline()
    fh.close()
    return content



class _abstractState( object ):
    
    def __init__(self, uri = None , domTree = None):
        if uri:
            if uri[-10:] == "index.xml":
                uri = uri[:-10]
            self.uri =  uri.lstrip( os.path.sep ) #the uri of the directory
            self._MyUri = normUri( uri )
            protocol , host , path, a,b,c = urlparse.urlparse( self._MyUri )

            if protocol == 'http':
                self._islocal = False
                indexUri = self._MyUri + "/index.xml"
            else:
                if self._MyUri.find( _cfg.results_path() ) == -1:
                    msg = "the "+ str( self._MyUri ) + " is not a Mobyle directory "
                    js_log.error( msg )
                    raise MobyleError, msg

                if not os.path.exists( self._MyUri ):
                    msg = "no such file or directory : "+ str( self._MyUri )
                    js_log.error( msg )
                    raise MobyleError, msg

                if not os.path.isdir( self._MyUri ):
                    msg = self._MyUri + " is not a directory"
                    js_log.error( msg )
                    raise MobyleError , msg

                indexUri = os.path.join( self._MyUri , "index.xml" )
                self._islocal= True
            self.indexName = indexUri

            try:
                self._parse()
            except IOError , err:
                if self._islocal:
                    self._createDocument()
                else:
                    msg = "can't create index file "+str( err )
                    js_log.error( msg )
                    raise MobyleError , msg
        elif domTree is not None:
            self.doc = domTree
            self.root = self.doc.getroot()
        else:
            msg = "you should provide either an uri or a dom tree"
            js_log.error( msg )
            raise MobyleError , msg
    

    def _parse(self):
        """
        parse a xml string or a file containing a xml tree
        """
        parser = etree.XMLParser( no_network = False )
        self.doc = etree.parse( self._MyUri + "/index.xml" , parser)
        self.root = self.doc.getroot()
        

    def update(self):
        """
        update the document the file index.xml
        """
        self._parse()


    def _updateNode(self, node , nodeName , content ):
        """
        replace the content of the text_node child of a node by content. if the node nodeName doesn't exist, it make it
        @param nodeName: the name of the Node to update
        @type nodeName: String
        @param content: the content of the text-node child of nodeName
        @type content: String
        """
        nodes = node.xpath( "./" + nodeName )
        if nodes:
            node2update = nodes[0]
            node2update.text = content
        else:  
            newNode = etree.Element( nodeName )
            newNode.text = str( content )
            node.append( newNode )
        

    def _addTextNode( self, node , nodeName , content , attr = None):
        """ 
        add a text node named nodeName with content to the node node
        @param node: the node on which the new node will append 
        @type node: node element
        @param nodeName: the name of the new node
        @type nodeName: string
        @param content: the content of the new node
        @type content: string
        """
        if attr:
            newNode = etree.Element( nodeName  ,  dict( zip( attr.keys() , map( str , attr.values() ) )))
        else:
            newNode = etree.Element( nodeName )
        try:
            newNode.text = str( content )
        except UnicodeEncodeError , err :
            js_log.error( nodeName + " : "+ str( err )  )
            raise err
        except Exception , err:
            js_log.error( "node: %s , content: %s : %s"%( nodeName, content , err ) , exc_info = True )
            raise MobyleError , err
        node.append( newNode )


    def commit( self ):
        """
        write into the file index.xml in the working directory 
        """
        if self._MyUri.find("http://") != -1:
            raise MobyleError, "can't modify a distant xml"
        else:
            try:
                tmpFile = open( "%s.%d" %(self.indexName , os.getpid() )  , 'w' )
                utils_indent( self.doc.getroot() )
                tmpFile.write( etree.tostring( self.doc , xml_declaration=True , encoding='UTF-8' )) 
                tmpFile.close()
                os.rename( tmpFile.name , self.indexName )
            except IOError, err:
                js_log.error( "IOError during write index.xml on disk")
                raise MobyleError ,err

    def isLocal(self):
        return self._islocal
     
    def _createDocument( self ):
        self.root = etree.Element( "jobState" )
        self.doc = etree.ElementTree( self.root )
        self.root.addprevious(etree.ProcessingInstruction('xml-stylesheet','href="/portal/xsl/job.xsl" type="text/xsl"'))

    def getOutputs( self ):
        """
        @return: a list of tuples or None
                  -each tuple is composed with 2 elements a parameterName and a list of files
                  -each file is a tuple with the file name and the size  
        @rtype: [ ( string parameterName , [ (string fileName , long size ) , ...) , ... ]
        """
        self._parse( )
        outputNodes = self.root.findall( "./data/output" )
        res = []
        
        for outputNode in outputNodes:
            parameterName = outputNode.find( 'parameter/name' ).text                 
            files =[]
            fileNodes = outputNode.findall( "./file" )
            for fileNode in fileNodes:
                filename = fileNode.text
                file_attr = fileNode.attrib
                size = file_attr[ "size" ]
                files.append( ( str( filename ) , long( size ) ) )
            res.append( ( parameterName , files ) )
        if res:
            return res
        else:
            return None
  
            
    def getOutput( self , parameterName ):
        """
        @param parameterName: the name of a parameter which produce result
        @type parameterName: string
        @return: a list containing the results filename , size and format . if there isn't any result for this parameter, return None
        @rtype:  [ ( string filename , long size , string fmt or None ) , ... ]
        """
        self._parse( )
        fileNodes = self.root.xpath( "./data/output[ parameter/name = '" + parameterName + "' ]/file" )
        
        files =[]
        for fileNode in fileNodes:
            filename =  fileNode.text 
            size = long( fileNode.get( 'size' ) )
            fmt = fileNode.get( "fmt" , None ) 
            if fmt :
                fmt = str( fmt )
            files.append( ( filename , size , fmt ) )
        if files:
            return files
        else:
            return None


    def getInputFiles( self ):
        """
        @return: a list of tuples or None
                  -each tuple is composed with 2 elements, a parameter and a list of files
                  -each file is a tuple of 3 elements with the file name , the size and the format if it's known or None 
        @rtype: [ ( parameter , [ (str fileName , int size, str format or None ) , ...) , ... ]
        """
        self._parse( )
        inputNodes = self.root.findall( "./data/input")
        res = []
        
        for inputNode in inputNodes:
            parameterNode = inputNode.find( 'parameter' )
            parameterName = parameterNode.find( 'name').text
            fileNodes = inputNode.findall( "./file" )
            if fileNodes:
                files =[]
                formattedFileNodes = inputNode.findall( "./formattedFile" )
                fileNodes += formattedFileNodes

                for fileNode in fileNodes:
                    fileName= str( fileNode.text )
                    size = long( fileNode.get( "size" ) )
                    fmt = fileNode.get( "fmt" , None ) 
                    if fmt :
                        fmt = str( fmt )
                    files.append( ( fileName , size , fmt ) )
                res.append( ( parameterName , files ) )
        if res:
            return res
        else:
            return None
        
           
            
    def getDir( self ):
        """
        @return: the absolute path to the directory where the job is executed
        @rtype: string
        @raise: MobyleError when the jobID is not local
        """
        if  self._islocal :
            return self._MyUri
        else:
            raise MobyleError, "it's not a local job :" + self._MyUri
    
    def getID( self ):
        """
        @return: the id of the job 
        @rtype: string
        """
        try:
            self._parse()
            return  self.root.find( "./id" ).text  
        except AttributeError:
            msg = "the element \"id\", doesn't exist"
            js_log.error( msg )
            raise MobyleError , msg
    
    def setID( self , ID ):
        """
        set the node id or if this node doesn't exist make it
        @param id: the job identifier (the url corresponding to the working directory). 
        @type id: String:
        """
        self._updateNode( self.root , 'id' , ID )

        
    def getSessionKey( self ):
        """
        @return: the key of the session
        @rtype: string
        """
        self._parse()
        sk = self.root.find( "./sessionKey")
        if sk is None:
            return None 
        else:
            return sk.text

    def setSessionKey( self , sessionkey ):
        """
        Set the sessionkey of this workflow to sessionkey
        @param sessionkey: the sessionkey of this workflow
        @type sessionkey: string
        """
        self._updateNode( self.root , 'sessionKey' , sessionkey )
        
    def getName( self ):
        """
        @return: the url corresponding to the service definition used for this job
        @rtype: string
        """
        self._parse()
        name = self.root.find("./name" )
        if name is not None:
            return name.text
        else:
            msg = "the element: \"name\" doesn't exist"
            js_log.error( msg )
            raise MobyleError , msg


    def setName( self , name):
        """
        update the node name or if this node doesn't exist make it
        @param name: the url of the service definition used for this job. 
        @type name: String:
        """
        self._updateNode( self.root , 'name' , name )
            

    def getDate( self):
        """
        @return: the date of the job the date format is: "%x %X"
        @rtype: string
        """
        self._parse()
        date = self.root.find("./date")
        if date is not None:
            return date.text
        else:
            msg = "the element: \"date\" doesn't exist"
            js_log.error( msg )
            raise MobyleError , msg


    def setDate( self, date= None):
        """
        update the node date or if this node doesn't exist make it
        @param date: the date. 
        @type date: String:
        """
        if date is None:            
            date = strftime( "%x  %X", localtime() )

        if type( date ) == types.StringType :
            date = strptime(  date , "%x  %X")
        else: # I assume the date is a <type 'time.struct_time'>
            date = strftime( "%x  %X", date )

        self._updateNode( self.root , 'date' , date )
        
        
    def getEmail( self):
        """
        @return: the email of the user
        @rtype: string
        """
        self._parse()
        email = self.root.find("./email")
        if email is not None:
            return email.text
        else:
            return None
        
    
    def setEmail( self, email ):
        """
        set the node email or if this node doesn't exist, make it
        @param email: the email user for this job. 
        @type email: String:
        """
        self._updateNode( self.root , 'email' , str( email ) )

    def getOutputFile( self, fileName ):
        """
        @param fileName:
        @type fileName: String
        @return: the content of a output file as a string
        @rtype: string
        """
        return getContentFile( self._MyUri + "/" + fileName )


    def open( self, fileName ):
        """
        return an file object if the file is local or a file like object if the file is distant
        we could apply the same method on this object: read(), readline(), readlines(), close(). (unlike file the file like object doesn't implement an iterator).
        @param fileName: the name of the file (given by getResults).
        @type fileName: string
        @return: a file or file like object
        """
        if self._islocal :
            try:
                fh = open( os.path.join( self._MyUri, fileName ), 'r' )
            except IOError, err:
                raise MobyleError ,err
        else:
            try:
                fh = urllib2.urlopen( self._MyUri +'/'+ fileName )
            except urllib2.HTTPError,err:
                raise MobyleError ,err
        return fh

    def setHost( self, host ):
        """
        update the node host or if this node doesn't exist make it
        @param host: the host of the job. 
        @type host: String:
        """
        self._updateNode( self.root , 'host' , host  )

    def setInputDataFile( self , paramName , File , fmtProgram = None  , formattedFile = None ):
        """
        if the node result exist add new nodes for files, otherwise create a new node results and add nodes for files
        @param paramName: the parameter name to update or create
        @type paramName: string
        @param files: a tuple of fileName , size , the data format
        @type files: list of tuple ( string fileName , int , string format or None )
        @param fmtProgram: the name of the program used to reformat the data
        @type fmtProgram:  string
        @param formattedFile: the file after reformatting
        @type formattedFile: a tuple of ( string fileName , long size , string data format )
        """
        try:
            inputNode = self.root.xpath( './data/input/parameter[ name = "'+ paramName + '" ]')[0]
            raise MobyleError , "this input data already exist " + paramName  
        except IndexError :
            #js_log.debug( "setInputDataFile pas d'input parameter avec le nom %s " %paramName)
            dataNode = self.root.find( './data' )
            if dataNode is None:
                #js_log.debug( "pas de noeud data" )
                dataNode = etree.Element( 'data' )
                self.root.append( dataNode )
            
            inputNode = self._createInOutNode( 'input', paramName )
            #js_log.debug( "1 nouvel inputNode a ete cree" )
            dataNode.append( inputNode )
            
            fileName , size , fmt = File
            attr = {}
            attr[ 'size' ] = str( size ) 
            if fmt :
                attr[ 'fmt' ] = fmt
            self._addTextNode( inputNode , 'file' , os.path.basename( fileName ) , attr )    
            if fmtProgram :
                self._addTextNode( inputNode , 'fmtProgram' , fmtProgram )
            if formattedFile :
                formattedFileName , formattedSize , formattedFmt = formattedFile
                attr = {}
                attr[ 'size' ] =  str( formattedSize )
                if formattedFmt :
                    attr[ 'fmt' ] = formattedFmt
                self._addTextNode( inputNode , 'formattedFile' , os.path.basename( formattedFileName ) , attr  )
                
                
    def renameInputDataFile(self , paramName , newName ):
        """
        Change the name of an infut file
        @param paramName: the parameter name 
        @type paramName: string
        @param newName: the new value of the input file name
        @type newName: string
        """
        try:
            inputNode = self.root.xpath( './data/input[parameter/name = "'+ paramName + '" ]')[0]
        except IndexError :
            raise MobyleError, "try to rename an unkown Input File parameter: %s" %paramName
        
        fileNode = inputNode.find( './file' )
        try:
            fileNode = inputNode.xpath( './formattedFile' )[0]
        except IndexError:
            pass
        fileNode.set( 'origName' , fileNode.text )
        fileNode.text = newName
        
        
    def setInputDataValue( self , paramName , value  ):
        """
        if the node result exist add new nodes for files, otherwise create a new node results and add nodes for files
        @param paramName: the parameter name to update or create
        @type paramName: string
        @param prompt: the prompt L{Parameter} of this parameter
        @type prompt: ( string prompt , string lang )
        @param paramType: the parameter Type 
        @type paramType: a MobyleType instance
        @param files: a fileName or a sequence of fileName
        @type files: a String or a sequence of Strings
        """
        try:
            inputNode = self.root.xpath( './data/input/parameter[ name = "'+ paramName + '" ]')[0]
            raise MobyleError , "this input data already exist " + paramName
        except IndexError :
            dataNode = self.root.find( './data' )
            if dataNode is None:
                dataNode = etree.Element(  'data' )
                self.root.append( dataNode )
            inputNode = self._createInOutNode( 'input', paramName )
            
            firstoutputNode = self.root.find( './data/output')
            if firstoutputNode is not None:
                firstoutputNode.addprevious( inputNode )
            else :
                dataNode.append(inputNode)
            try:
                self._addTextNode( inputNode , 'value' , str( value ) )
            except Exception, err:
                js_log.error( "cannot add '%s' for parameter %s : %s" %( value , paramName , err ) )
                from Mobyle.StatusManager import StatusManager
                from Mobyle.Status import Status
                if self._islocal:
                    sm = StatusManager()
                    dirPath = self._MyUri
                    sm.setStatus( dirPath , Status( code = 5 , message = 'Mobyle Internal Error' ) )
                raise MobyleError( 'Mobyle Internal Error' ) 
    
    
    def setOutputDataFile( self , paramName , files , isstdout = False ):
        """
        if the node result exist add new nodes for files, otherwise create a new node results and add nodes for files
        @param paramName: the parameter name to update or create
        @type paramName: string
        @param files: a list where each element are composed of 3 item ( fileName , size , format )
        @type files: [ ( string , int , string or None ) , ... ] 
        """
        try:
            outputNode = self.root.xpath( './data/output/parameter[ name = '+ paramName + ' ]')[0]
            raise MobyleError , "this output data already exist " + paramName
        except IndexError :
            dataNode = self.root.find( './data' )
            if dataNode is None:
                dataNode = etree.Element( 'data' )
                self.root.append( dataNode )
            
            if isstdout:
                outputNode = self._createInOutNode( 'output', paramName , paramAttrs = {'isstdout' : '1' } )
            else:
                outputNode = self._createInOutNode( 'output', paramName  )
            dataNode.append( outputNode )
        for File in files:
            filename , size , fmt = File
            attr = {}
            attr[ 'size' ] = str( size )
            if fmt:
                attr [ 'fmt' ] = fmt
            self._addTextNode( outputNode , 'file' , os.path.basename( filename ) , attr = attr )
              
                    
    def _createInOutNode( self , io , paramName , paramAttrs = {} ):
        if io != 'input' and io != 'output' :
            raise MobyleError , "io could take only 'input' or 'output' as value"
        inOutputNode = etree.Element( io )
        parameterNode = self._createParameter(  paramName , attrs = paramAttrs)
        inOutputNode.append( parameterNode )
        return inOutputNode
 
    def _createParameter( self , paramName , attrs = {}):       
        newParameterNode = etree.Element( "parameter" )
        if attrs :
            attributes = newParameterNode.attrib
            attributes.update( str( attrs ) )
        self._addTextNode( newParameterNode , 'name' , paramName )
        return newParameterNode

    def delInputData( self , paramName ):
        try:
            inputDataNode = self.root.xpath( "./data/input[ parameter/name = '" + paramName + "' ]")[0]
        except IndexError:
            raise MobyleError, "there is no data with parameter named:" + str( paramName )            
        else:
            dataNode = self.root.find( "./data")
            dataNode.remove( inputDataNode )

    def getArgs( self ):
        """
        @return: 
        @rtype:
        """
        inputDataNodes = self.root.findall( './data/input' )
        args = {}
        
        for inputDataNode in inputDataNodes:
            """
            toutes les valeurs meme les noms de fichiers
            nom : value
            """
            value = inputDataNode.find( './value' )
            if value is not None :
                value = value.text
            else:
                value = inputDataNode.find( './formattedFile')
                if value is not None:
                    value = value.text
                else:
                    value = inputDataNode.find( './file')
                    if value is not None:
                        value = value.text
                    else:
                        raise MobyleError , "this input has not value nor file"
            name = inputDataNode.find( './parameter/name').text
            args[ name ] = value
        return args     
               
    
    def getPrompt( self , paramName ):
        """
        @param paramName: a parameter name
        @type paramName: string
        @return: the prompt of this parameter
        @rtype: string
        """
        try:
            prompt = self.root.xpath( './data/*/parameter[ name = "' + paramName + '"]/prompt/text()' )[0]
            return prompt
        except IndexError:
            return None
    
    
    def getFormattedData( self ):
            """
            for input files return a dict like cas des input files uniquement
                  file: valeur
                  fileFmt: valeur
                  program: valeur
                  formattedFile: valeur
                  formattedFileFmt: valeur
            """
            inputFileNodes = self.root.xpath( './data/input[ file ]' )
            fdata = {}
            
            for inputFileNode in inputFileNodes:
                name = inputFileNode.find( './parameter/name' ).text
                FileName = inputFileNode.find( './file').text
                fileFmt = inputFileNode.xpath( './file/@fmt' )[0]
                program = inputFileNode.find( './fmtProgram').text
                try:
                    formattedFile = inputFileNode.xpath( './formattedFile/text()' )[0]
                    formattedFileFmt = inputFileNode.xpath( './formattedFile/@fmt')[0]
                except IndexError:
                    formattedFile = None
                    formattedFileFmt = None
                
                fdata[ name ] = { 'file'            : FileName,
                                 'fileFmt'          : fileFmt,
                                 'fmtprogram'       : program,
                                 'formattedFile'    : formattedFile,
                                 'formattedFileFmt' : formattedFileFmt 
                                 }
            return fdata

class JobState( object ):
    """
    the JobState Object manage the informations in index.xml file
    G{}
    """
    _refs = {}
    
    def __new__( cls , uri = None , service = None ):

        state = None
        if uri is None:
            uri = os.getcwd()
        if uri[-9:] == "index.xml":
            uri = uri[:-9]
        uri = uri.rstrip( '/' )
        MyUri = normUri( uri ) 
        protocol , _ , _ , _ , _ , _ = urlparse.urlparse( MyUri )
        if protocol == 'http':
            islocal = False
            indexUri = MyUri + "/index.xml"
        else:
            results_path = _cfg.results_path() 
            if MyUri.find( results_path ) == -1:
                msg = "the "+ str( MyUri ) + " is not a Mobyle jobs directory "
                js_log.error( msg )
                from errno import EINVAL
                raise JobError( EINVAL , "not a Mobyle jobs directory" , MyUri )
            if not os.path.exists( MyUri ):
                import sys
                msg = "call by %s : no such directory : %s" %( os.path.basename( sys.argv[0] ) , MyUri )
                js_log.error( msg )
                from errno import ENOENT
                raise JobError( ENOENT , "No such directory" , MyUri )
            if not os.path.isdir( MyUri ):
                msg = MyUri + " is not a directory"
                js_log.error( msg )
                from errno import ENOTDIR
                raise JobError( ENOTDIR , "not a directory" , MyUri )
            indexUri = os.path.join( MyUri , "index.xml" )
            islocal = True
        try:
            return cls._refs[ MyUri ]
        except KeyError:
            self = super( JobState , cls ).__new__( cls )
            self.state = state
            self.uri = uri        #uri given by the user
            self._MyUri = MyUri   #path if uri = local url if uri is distant
            self._islocal = islocal
            if self._islocal and not os.path.exists( indexUri ):
                if service is not None:
                    self.createState( service )
                else:
                    raise MobyleError , "%s does not exists" %indexUri
       
            else:
                try:
                    parser = etree.XMLParser( no_network = False )
                    doc = etree.parse( indexUri , parser )
                except Exception ,err:
                    raise MobyleError , "problem in parsing %s : %s" %( indexUri , err )
                root = doc.getroot()
                if len(root.xpath('workflow'))>0:
                    self.state = WorkflowJobState( domTree = doc )
                else:
                    self.state = ProgramJobState( domTree = doc )

            self.state.uri = self.uri
            self.state._MyUri = self._MyUri
            self.state.indexName = indexUri  
            self.state._islocal = self._islocal

            cls._refs[ MyUri ] = self
            return self
        

    def __getattr__( self , name ):
        if self.state :
            return getattr( self.state , name )
        else:
            msg = "Jobstate instance is empty. you must create a State before"
            raise MobyleError , msg


    def createState( self , service ):
        if self.state :
            msg = "cannot create a JobState, Jobstate already exists"
            raise MobyleError , msg
        else:
            if isinstance(service, Program):
                if self._islocal:
                    self.state = ProgramJobState( uri = self._MyUri )
                    self.state.setDefinition( service.getUrl())
                else:
                    msg ="can't create a State on a distant Mobyle Server"
                    raise MobyleError , msg
            elif isinstance(service, Workflow):
                if self._islocal:
                    self.state = WorkflowJobState( uri = self._MyUri )
                    self.state.setDefinition(service)
                else:
                    msg ="can't create a State on a distant Mobyle Server"
                    raise MobyleError , msg
            else:
                raise MobyleError 

    def getWorkflowID( self ):
        """
        @return: the url of the worklow owner of this job.
        @rtype: string
        """
        self._parse()
        wf = self.root.find( "./workflowID" )
        if wf is None:
            return None
        else:
            return wf.text


    def setWorkflowID( self , worklowID ):
        """
        update the node worklowID or if this node doesn't exist, make it
        @param worklowID: the url of the worklow owner of this job. 
        @type worklowID: String:
        """
        self._updateNode( self.root , 'workflowID' , worklowID )
##############################################
#                                            #
#               ProgramJobState              #
#                                            #
##############################################


class ProgramJobState( _abstractState ):
    """
    ProgramJobState Object manages the information in index.xml file for a program job
    """
    def isWorkflow(self):
        return False
    
    def setDefinition( self , program_url ):
        """Copy the program definition in the program job for future reference"""
        from Mobyle.Registry import registry
        #                    /data/services/servers/SERVER/programs/PROGRAM_NAME.xml  
        match = re.search(  "/data/services/servers/(.*)/.*/(.*)\.xml" , program_url )
        server_name = match.group(1)
        service_name = match.group(2)
        try:
            program_path = registry.getProgramPath( service_name , server_name )
        except KeyError:
            raise MobyleError( "registry have no service %s for server %s" %(service_name , server_name )) 
        program_def  = etree.parse( program_path )
        program_node = program_def.getroot()
        #if a node 'program already exists , remove it bfore to add the new one
        nodes = self.root.xpath( 'program' )
        if nodes:
            p = nodes[0].getparent()
            for i in nodes:
                p.remove(i)  
        self.root.insert(0, program_node )
        
    
    def getDefinition(self):
        """Copy the program definition in the program job for future reference"""
        nodes = self.root.xpath( 'program' )
        if nodes:
            return nodes[0]
        else:
            return None
    
    def getCommandLine( self ):
        """
        @return: the Command line
        @rtype: string
        """
        self._parse()
        cl = self.root.find( "./commandLine" )
        if cl is None:
            return None
        else:
            return cl.text


    def setCommandLine( self , command ):
        """
        update the node command or if this node doesn't exist, make it
        @param command: the command of the job. 
        @type command: String:
        """
        self._updateNode( self.root , 'commandLine' , command )

    def getStdout( self ):
        """
        we assume that the standart output was redirect in programName.out
        @return: the content of the job stdout as a string
        @rtype: string
        @raise MobyleError: if the job is not finished a L{MobyleError} is raised
        """
        try:
            outName = self.root.xpath( './data/output/parameter[@isstdout=1]/name/text()' )[0]
        except IndexError:
            outName = os.path.join( self._MyUri , os.path.basename(self.getName())[:-4] + ".out" )
        return getContentFile( outName )
    

    def getStderr( self ):
        """
        @return: the content of the job stderr as a string
        @rtype: string
        @raise MobyleError: if the job is not finished a L{MobyleError} is raised
        """
        try:
            errname = os.path.join( self._MyUri , os.path.basename(self.getName())[:-4] + ".err" )
        except KeyError:
            return None
        return getContentFile( errname )

    def getParamfiles(self):
        """
        @return: a list containing the results filename. if there isn't any result return None
        @rtype: list of tuple ( string filename , long size )
        """
        self._parse( )
        results = []
        for paramf in self.root.findall( "./paramFiles/file" ):
            filename = paramf.text
            size = paramf.get( "size" )
            results.append( ( str( filename ) , long( size ) ) )
        return results


    def setParamfiles( self , files ):
        """
        if the node result exist add new nodes for files, otherwise create a new node results and add nodes for files
        param files: a list of fileName , size of file
        type files: [ ( String fileName , Long size ) , ... ]
        """
        paramfiles_node = self.root.findall( './paramFiles' )
        lastChild = self.root.findall( './*' )[-1]
        
        if paramfiles_node:
            paramfiles_node  = paramfiles_node[0]
        else:
            paramfiles_node = etree.Element( 'paramFiles' )
            if lastChild.tag == 'commandLine':
                lastChild.addprevious( paramfiles_node )
            else:
                self.root.append( paramfiles_node )
        for File in files:
            fileName , size = File
            attr = {}
            attr[ 'size' ] = size
            self._addTextNode( paramfiles_node , 'file', fileName , attr )

    def getStatus(self):
        raise NotImplementedError , "ProgramState does not manage status anymore use StatusManager instead"


    def setStatus(self):
        raise NotImplementedError , "ProgramState does not manage status anymore use StatusManager instead"



class WorkflowJobState( _abstractState ):
    """
    WorkflowJobState Object manages the information in index.xml file for a workflow job
    """

    def isWorkflow(self):
        return True
        
    def setDefinition(self, workflow):
        """Copy the workflow definition in the workflow job for future reference"""
        nodes = self.root.xpath( 'workflow' )
        if nodes:
            p = nodes[0].getparent()
            for i in nodes:
                p.remove(i)        
        self.root.append(copy.deepcopy(workflow))
    
    def getDefinition(self):
        """Copy the workflow definition in the workflow job for future reference"""
        nodes = self.root.xpath( 'workflow' )
        return nodes[0]
        
    def setTaskJob(self, task, jobId):
        """Set the job that runs a specific task"""
        nodes = self.root.xpath( 'jobLink[@taskRef="%s"]' % task.id)
        if nodes:
            p = nodes[0].getparent()
            for i in nodes:
                p.remove(i)      
        jobLinkElNode = etree.Element("jobLink")
        jobLinkElNode.set("taskRef",task.id)
        jobLinkElNode.set("jobId",jobId)
        self.root.append( jobLinkElNode )
        
    def getTaskJob(self, task):
        """Get the job that runs a specific task"""
        res = self.root.xpath( 'jobLink[@taskRef="%s"]/@jobId' % task.id)
        if len(res)>0:
            return res[0]

    def getSubJobs(self):
        """Get all the corresponding subjobs information"""
        subjobs = []
        res = self.root.xpath( 'jobLink')
        for entry in res:
            jobID = entry.xpath('@jobId')[0]
            taskID = entry.xpath('@taskRef')[0]
            task = self.root.xpath('workflow/flow/task[@id="%s"]' % taskID)[0]
            serviceName = task.xpath('@service')[0]
            try:
                job = JobState(jobID)
                subjobs.append({'jobID':jobID,
                                'userName':jobID,
                                'programName':serviceName,
                                'date':strptime( job.getDate() , "%x  %X"),
                                'owner':self.getID()
                                })
            except MobyleError, me:
                # this happens if the job index.xml file cannot be retrieved, especially if it is a removed subtask (e.g., remote)
                pass
            
        return subjobs