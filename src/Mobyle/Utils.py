########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################


#import os 
#from time import localtime, strftime , strptime

from logging import getLogger
u_log = getLogger( __name__ )

from Mobyle.MobyleError import MobyleError , UserValueError
from Mobyle.Admin import Admin



def executionLoader( jobID = None , alias = None , execution_config=None):
    assert ( bool( jobID ) +  bool( alias ) + bool( execution_config )== 1), "please provide either a jobID, an alias or an execution_config"
    from Mobyle.ConfigManager import Config
    cfg = Config()
    if not execution_config:
        if jobID:
            from Mobyle.JobState import normUri
            from urlparse import urlparse
            path = normUri( jobID )
            protocol, host, path, a, b, c = urlparse( path )
            if protocol == "http":
                raise  NotImplementedError , "trying to instanciate an Execution system from a remote Job"
            if path[-9:] == "index.xml":
                path = path[:-10 ]
            adm = Admin( path )
            alias = adm.getExecutionAlias()
        if not alias:
            msg = "cant determine the Execution system for %s " % ( jobID ) 
            u_log.error( msg )
            raise MobyleError( msg )
        try:
            execution_config = cfg.getExecutionConfigFromAlias( alias )
        except KeyError:
            msg = "the ExecutionConfig alias %s doesn't match with any alias in Config" % alias
            u_log.critical( msg )
            raise MobyleError( msg )     
    klass_name = execution_config.execution_class_name
    try:
        module = __import__( 'Mobyle.Execution.%s' % klass_name )
    except ImportError , err:
        msg = "The Execution.%s module is missing" % klass_name
        u_log.critical( msg )
        raise MobyleError, msg
    except Exception , err:
        msg = "an error occurred during the Execution.%s import: %s" % ( klass_name , err )
        u_log.critical( msg )
        raise MobyleError, msg
    try:
        klass = module.Execution.__dict__[ klass_name ].__dict__[ klass_name ]
        return klass( execution_config )
    except KeyError , err :
        msg = "The Execution class %s does not exist" % klass_name
        u_log.critical( msg )
        raise MobyleError, msg
    except Exception , err:
        msg = "an error occurred during the class %s loading : %s" % ( klass_name, err )
        u_log.critical( msg )
        raise MobyleError, msg
    
    
def getStatus( jobID ):
    """
    @param jobID: the url of the job
    @type jobID: string
    @return: the current status of the job
    @rtype: string
    @raise MobyleError: if the job has no number or if the job doesn't exist anymore
    @raise OSError: if the user is not the owner of the process
    """
    from Mobyle.JobState import JobState , normUri
    from urlparse import urlparse
    from Mobyle.StatusManager import StatusManager 
    
    path = normUri( jobID )
    protocol, host, path, a, b, c = urlparse( path )
    if protocol == "http":
        raise  NotImplementedError , "trying to querying a distant server"
    
    if path[-9:] == "index.xml":
        path = path[:-10 ]
    sm =StatusManager()
    
    oldStatus = sm.getStatus( path )
    #'killed' , 'finished' , 'error' the status cannot change anymore
    #'building' these jobs have not yet batch number

    #  ( 'finished' , 'error' , 'killed' , 'building' ):
    if not oldStatus.isQueryable():
        return oldStatus
    else: 
        adm = Admin( path )
        batch = adm.getExecutionAlias()
        jobNum = adm.getNumber()
        
        if batch is None or jobNum is None:
            return oldStatus
        try:
            exec_engine = executionLoader( jobID = jobID )
            newStatus = exec_engine.getStatus( jobNum )
        except MobyleError , err : 
            u_log.error( str( err ) , exc_info = True )
            raise err
        if not newStatus.isKnown():
            return oldStatus
        if newStatus != oldStatus :
            sm.setStatus( path , newStatus )
        return newStatus 

def isExecuting( jobID ):
    """
    @param jobID: the url of the job
    @type jobID: string
    @return True if the job is currently executing ( submitted , running , pending , hold ).
    False otherwise ( building, finished , error , killed )
    @rtype: boolean
    @raise MobyleError: if the job has no number 
    @raise OSError: if the user is not the owner of the process
    """
    from Mobyle.JobState import normUri
    from urlparse import urlparse 
    from Mobyle.StatusManager import StatusManager
    
    path = normUri( jobID )
    protocol, host, path, a, b, c = urlparse( path )
    if protocol == "http":
        raise  NotImplementedError , "trying to querying a distant server"
    
    if path[-9:] == "index.xml":
        path = path[:-10 ]
    adm = Admin( path )
    batch = adm.getExecutionAlias()
    jobNum = adm.getNumber()
    
    if batch is None or jobNum is None:
        sm = StatusManager()
        status = sm.getStatus( path )
        if not status.isQueryable():
            return False
        else:
            raise MobyleError( "inconsistency in .admin file %s" % path )
    try:
        execKlass = executionLoader( jobID = jobID )
        newStatus = execKlass.getStatus( jobNum )
    except MobyleError , err : 
        u_log.error( str( err ) , exc_info = True )
        raise err
    return newStatus.isQueryable()





def killJob( jobID ):
    """
    @param jobID: the url of the job or a sequence of jobID
    @type jobID: string or sequence of jobID
    @return: 
    @rtype: 
    @raise MobyleError: if the job has no number or if the job doesn't exist anymore
    @todo: tester la partie sge
    """
    from types  import StringTypes , TupleType , ListType
    from Mobyle.MobyleError import MobyleError
    from Mobyle.JobState import JobState , normUri
    from Mobyle.Job import Job
    from Mobyle.WorkflowJob import WorkflowJob
    
    if isinstance( jobID , StringTypes ) :
        jobIDs = [ jobID ]
    elif isinstance( jobID , ( ListType , TupleType ) ) :
        jobIDs = jobID
    else:
        raise MobyleError , "jobID must be a string or a Sequence of strings :%s"%type( jobID )
    
    errors = []
    for jobID in jobIDs :
        try:
            path = normUri( jobID )
        except MobyleError , err :
            errors.append( ( jobID , str( err ) ) )
            continue
        if path[:4] == 'http' :
            #the jobID is not on this Mobyle server
            errors.append( ( jobID , "can't kill distant job" ) )
            continue
        js = JobState(uri = jobID )
        if js.isWorkflow():
            job = WorkflowJob( id= jobID )
        else:
            job= Job( ID= jobID )
        try:
            job.kill()
        except MobyleError , err :
            errors.append( ( jobID , str( err ) ) )
            continue
    if errors:
        msg = ''
        for jobID , msgErr in errors :
            msg = "%s killJob( %s ) - %s\n" % ( msg , jobID , msgErr )
            
        raise MobyleError , msg

def safeFileName( fileName ):
    import string , re
    
    if fileName in ( 'index.xml' , '.admin' , '.command' ,'.forChild.dump' ,'.session.xml'):
        raise UserValueError( msg = "value \"" + str( fileName ) + "\" is not allowed" )
    
    for car in fileName :
        if car not in string.printable : #we don't allow  non ascii char
            fileName = fileName.replace( car , '_')
    
    #SECURITY: substitution of shell special characters
    fileName = re.sub( "[ #\"\'<>&\*;$`\|()\[\]\{\}\?\s ]" , '_' , fileName )
                  
    #SECURITY: transform an absolute path in relative path
    fileName = re.sub( "^.*[\\\:/]", "" , fileName )
    
    return fileName



def makeService( programUrl ):
    import Mobyle.Parser
    try:
        service = Mobyle.Parser.parseService( programUrl )
        return service
    except IOError , err:
        raise MobyleError , str( err )

      
def sizeFormat( byte , precision= 2 ):
    """Returns a humanized string for a given amount of bytes"""
    import math
    byte = int( byte )
    if byte is 0:
        return '0 bytes'
    log = math.floor( math.log( byte , 1024 ) )
    return "%.*f%s" % ( precision , byte / math.pow(1024, log), [ 'bytes', 'KiB', 'MiB' , 'GiB' ][ int(log) ] )

def zipFiles( zip_filename , files ):
    """
    @param zip_filename: the absolute path to the archive to create
    @type zip_filename: string
    @param files: a list of tuple each tuple contains 2 elements the absolute path of the file to archive , and the name of this file in the archive
    @type files: [ ( string abs_path_file_to archive , string arc_name ) , ... ]
    @return: the abspath of the archive
    @rtype: string
    """
    import zipfile
    import os
    from time import localtime
    from Mobyle.StatusManager import StatusManager
    
    myZipFile = zipfile.ZipFile( zip_filename  , "w" )
    for filename , arc_filename in files:
        if arc_filename == 'index.xml':
            from lxml import etree
            index_tree = etree.parse( filename )
            status_tree = etree.parse( os.path.join( os.path.dirname(filename), StatusManager.file_name ) )
            root_index_tree = index_tree.getroot()
            pi = root_index_tree.getprevious()
            pi.set( "href" , "job.xsl")
            root_index_tree.append( status_tree.getroot() )
            indent( root_index_tree )
            index = etree.tostring( index_tree , xml_declaration=True , encoding='UTF-8' )
            myZipInfo = zipfile.ZipInfo( arc_filename , localtime()[:6] )
            myZipInfo.external_attr = 2175008768   # set perms to 644
            myZipFile.writestr(  myZipInfo  , index )
            continue
        try:
            size = os.path.getsize( filename )
        except OSError , err:
            u_log.critical( "error durring zipping files: %s"%(err) , exc_info = True)
            continue
        if size > 0 and size < 10 :
            myZipFile.write( filename   , arc_filename , zipfile.ZIP_STORED )
        elif size >= 10 and size < 2147483648 : #2Go 
            myZipFile.write(   filename   , arc_filename , zipfile.ZIP_DEFLATED )
        elif size >= 2147483648 :#2Go
            myZipInfo = zipfile.ZipInfo( arc_filename , localtime()[:6] )
            myZipInfo.external_attr = 2175008768   # set perms to 644
            myZipFile.writestr(  myZipInfo  , "Sorry this file result is too large ( > 2GiB ) to be included in this archive." )    
        else:
            #the file is empty we don't add it to this archive
            pass   
    myZipFile.close()
    return  zip_filename

def emailResults( cfg , userEmail, registry, ID, job_path, serviceName, jobKey, FileName = None ):
    """
    @param cfg: the configuration of Mobyle    
    @type cfg: Config instance
    @param userEmail: the user email address
    @type userEmail: EmailAddress instance
    @param registry: the registry of deployed services
    @type registry: Registry.registry object
    @param ID: the ID of the job
    @type ID: string
    @param job_path: the absolute path to the job 
    @type job_path: string
    @param serviceName: the name of the service
    @type serviceName: string
    @param jobKey: the key of the job
    @type jobKey: string
    @param FileName: the absolute path of zip file to attach to the email
    @type FileName: string or None
    """
    from Mobyle.Net import Email 
    from Mobyle.MobyleError import EmailError , TooBigError
    import os
    dont_email_result , maxmailsize =  cfg.mailResults()
    if dont_email_result :
        return
    else:
        if userEmail :
            mail = Email( userEmail )
            jobInPortalUrl = "%s/portal.py#jobs::%s" %( cfg.cgi_url() ,
                                                        registry.getJobPID( ID ),
                                                       )
            
            if FileName is not None:
                zipSize = os.path.getsize( FileName )
                mailDict = { 'SENDER'         : cfg.sender() ,
                             'HELP'           : cfg.mailHelp() ,
                             'SERVER_NAME'    : cfg.portal_url() ,
                             'JOB_URL'        : jobInPortalUrl , 
                             'RESULTS_REMAIN' : cfg.remainResults() ,
                             'JOB_NAME'       : serviceName ,
                             'JOB_KEY'        : jobKey ,
                             }
                if zipSize > maxmailsize - 2048 :
                    #2048 octet is an estimated size of email headers
                    try:
                        mail.send( 'RESULTS_TOOBIG' , mailDict )
                        return
                    except EmailError ,err :
                        msg = str(err)
                        adm = Admin( job_path )
                        adm.setMessage( msg )
                        adm.commit()
                        u_log.error( "%s/%s : %s" %( serviceName ,
                                                      jobKey ,
                                                      msg
                                                      )
                        )
                        return
                else:
                    try:   
                        mail.send( 'RESULTS_FILES' , mailDict , files = [ FileName ]  )
                        return
                    except TooBigError ,err :
                        try:
                            mail.send( 'RESULTS_TOOBIG' , mailDict )
                        except EmailError ,err :
                            msg = str(err)
                            adm = Admin( job_path )
                            adm.setMessage( msg )
                            adm.commit()
                            u_log.error( "%s/%s : %s" %( serviceName ,
                                                          jobKey ,
                                                          msg
                                                          )
                            )
                        
                        return
            else: #if there is a problem on zip creation
                mail.send( 'RESULTS_NOTIFICATION' , mailDict )
        else:
            return

    

def indent(elem, level=0):
    """
    Due to malfunction in pretty_print argument of etree.tostring
    we use this function found here
    http://stackoverflow.com/questions/1238988/changing-the-default-indentation-of-etree-tostring-in-lxml
    to have a correct indentation 
    """
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

#def parse_xml_file(file_handle, parser):
#    """
#    wrapper for the lxml etree.parse() function
#    the behavior of lxml.parse changes between v2.2 and v2.3:
#    in v2.3 it closes automatically the file after parsing it,
#    breaking the file-locking mechanism.
#    this function uses a workaround for versions 2.3.x
#    @param file_handle: the file handle for the XML file to be parsed
#    @type zip_filename: {file}
#    @param parser: parser object to pass to etree.parse
#    @type parser: {lxml.etree._BaseParser}
#    @return: the parsed document as an ElementTree object
#    @rtype: {lxml.etree._ElementTree}
#    """
#    from lxml import etree
#    if etree.__version__.startswith('2.3'):
#        from StringIO import StringIO
#        return etree.parse( StringIO(''.join(file_handle.readlines())) , parser )
#    else:
#        return etree.parse(file_handle)
#    