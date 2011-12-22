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
Registry.py

This module holds:
- The Registry class that describes the list of installed/imported services 
  and their servers
- The DefNode class, an abstract class that describes an element (node or
  leaf) of the services tree
- The ProgramDef class that describes a service (leaf in the services tree)
- The CategoryDef class that describes a category (node in the services tree)
- The ServerDef class that describes a server (node in the services tree)
"""
import os
from hashlib import md5
from glob import glob

from Mobyle.ConfigManager import Config
_cfg = Config()

from logging import getLogger
r_log = getLogger( __name__ )


class DefNode(object):
    """
    DefNode is the class that provides the tree structure to the 
    server/categories/program hierarchy
    """

    def __init__(self):
        self.name = None
        self.children = []
        self.parents = []
              
    def getDescendants(self):
        """
        Returns the descendants of the node recursively
        @return: the list of descendant nodes
        @rtype: list
        """
        r = []
        r.extend(self.children)
        for p in self.children:
            r.extend(p.getDescendants())
        return r

    def getAncestors(self):
        """
        Returns the ancestors of the node recursively
        @return: the list of ancestor nodes
        @rtype: list
        """
        r = []
        r.extend(self.parents)
        for p in self.parents:
            r.extend(p.getAncestors())
        return r

    def addDescendant(self, subpath):
        """
        Adds a descendant to the node, by recursively adding the descendants from the provided subpath if they do not exist
        @param subpath: the subpath, a list of descendant objects 
                        (e.g.: [CategoryDef, CategoryDef, ProgramDef])
        @type subpath: string
        """
        if len(subpath)==0:
            return
        else:
            c = [c for c in self.children if (c.name == subpath[0].name and (not(hasattr(c,'server')) or c.server == subpath[0].server))]
            if not(c):
                c = subpath[0]
                self.children.append(c)
                c.parents.append(self)
            else:
                c = c[0]
            c.addDescendant(subpath[1:])
            
    def __cmp__(self, other):
        """
        Comparison operator that allows to classify the tree structure alphabetically
        based on node names
        @param other: the other node to which self is compared
        @type other: DefNode
        @return: the comparison result
        @rtype: boolean
        """
        return cmp(self.name.lower(), other.name.lower())
    
    def getChildCategories(self):
        """
        Returns child categories, i.e. child nodes which happen to be CategoryDef instances
        @return: a list of category nodes
        @rtype: list
        """
        l = [c for c in self.children if not(isinstance(c, ServiceDef))]
        l.sort()
        return l

    def getChildServices(self):
        """
        Returns child programs, i.e. child nodes which happen to be ServiceDef instances
        @return: a list of program nodes
        @rtype: list
        """
        l = [c for c in self.children if isinstance(c, ServiceDef)]
        l.sort()
        return l

class Registry(DefNode):
    
    #__shared_state = {}
    
    def __init__( self ):
        #self.__dict__ = self.__shared_state
        DefNode.__init__(self)
        self.programs = []
        self.workflows = []
        self.viewers = []
        self.servers = []
        self.serversByName = {}
        self.serversByUrl = {}
        self.programsByUrl = {}
        self.workflowsByUrl={}
        self.viewersByUrl = {}
        self.servers_path=_cfg.servers_path()
    
    def load( self):
        """
        
        """
        serverProperties = self._getServerProperties()
        
        for name, properties in serverProperties.items():
            server = ServerDef( name = name,
                                url = properties[ 'url' ] ,
                                help = properties[ 'help' ],
                                repository = properties[ 'repository' ],
                                jobsBase = properties[ 'jobsBase' ] ,
                               )
            self.addServer(server)
            for name in properties[ 'programs' ]:
                try:                        
                    url = self.getProgramUrl( name, server.name )
                    path = self._computeProgramPath( name, server.name)
                    program = ProgramDef( name = name,
                                          url = url,
                                          path = path,
                                          server = server
                                        )
                    # service disabled
                    if _cfg.isDisabled( portalID = "%s.%s" %( server.name , program.name ) ): 
                        program.disabled = True
                    # service with restricted access
                    if not( _cfg.isAuthorized( url )):
                        program.authorized = False
                    self.addProgram( program )
                except IndexError, e:
                    r_log.error("Error while loading %s: %s" % (name, e))
            
            for name in properties[ 'workflows' ]:
                try:                        
                    url = self.getWorkflowUrl( name, server.name)
                    path = self._computeWorkflowPath( name, server.name)
                    wf = WorkflowDef( name = name,
                                          url = url,
                                          path = path,
                                          server = server
                                        )
                    # service disabled
                    if _cfg.isDisabled( portalID = "%s.%s" %( server.name , wf.name ) ): 
                        wf.disabled = True
                    # service with restricted access
                    if not( _cfg.isAuthorized( url )):
                        wf.authorized = False
                    self.addWorkflow( wf )
                except IndexError, e:
                    r_log.error("Error while loading %s: %s" % (name, e))
            
            
            if server.name == 'local':
                for name in properties['viewers']:
                    
                    try:                        
                        url = self.getViewerUrl( name )
                        path = self.getViewerPath( name )
                        viewer = ViewerDef( name= name,
                                       url= url,
                                       path=path,
                                       server=server
                                              )
                        self.addViewer(viewer)
                    except IndexError, e:
                        r_log.error("Error while loading %s: %s" % (name, e))

    def loadSessionServices( self, session):
        """ 
        This method allows to add BMW-defined workflows to the registry, so that
        they can be run in Mobyle
        """
        session_workflow_path_list = glob( os.path.join(session.getDir() , 'BMW','*.graphml' ) )
        session_workflow_list = [ (os.path.basename( p )[:-8],p) for p in session_workflow_path_list ]
        for sw in session_workflow_list:
            
            wf = WorkflowDef( name = sw[0],
                                  url = session.url+'/BMW/'+sw[0]+'_mobyle.xml',
                                  path = sw[1],
                                  server = self.serversByName['local']
                                )
            self.addWorkflow(wf)
    
    def addServer(self, server):
        self.servers.append( server )
        self.serversByName[ server.name ] = server
        self.serversByUrl[ server.url ] = server

    def addProgram( self, program ):
        self.programs.append( program )
        self.programsByUrl[ program.url ] = program
        self.serversByName[ program.server.name ].programs.append( program )
        self.serversByName[ program.server.name ].programsByName[ program.name ] = program
    
    def addWorkflow(self, workflow ):
        self.workflows.append( workflow )
        self.workflowsByUrl[ workflow.url ] = workflow
        self.serversByName[ workflow.server.name ].workflows.append( workflow )
        self.serversByName[ workflow.server.name ].workflowsByName[ workflow.name ] = workflow
    
    def addViewer(self, viewer ):
        self.viewers.append( viewer )
        self.viewersByUrl[ viewer.url ] = viewer
        self.serversByName[ viewer.server.name ].viewers.append( viewer )
        self.serversByName[ viewer.server.name ].viewersByName[ viewer.name ] = viewer
    
    def has_service(self , service ):
        """
        @param service: the service to test the existance.
        @type service: a ServiceDef instance
        @return: True if the service exists in this registry, False otherwise.
        @rtype: boolean.
        """
        if isinstance( service , ProgramDef ):
            try:
                self.serversByName[ service.server.name ].programsByName[ service.name ]
                return True
            except KeyError:
                return False
        elif isinstance( service , WorkflowDef ):
            try:
                self.serversByName[ service.server.name ].workflowsByName[ service.name ]
                return True
            except KeyError:
                return False
        elif isinstance( service , ViewerDef ):
            try:
                self.serversByName[ service.server.name ].viewersByName[ service.name ]
                return True
            except KeyError :
                return False


    def pruneService(self, service):
        """
        remove a Service Definition from the registry
        @param service: the Service to remove
        @type service: a ServiceDef instance
        """
        if isinstance( service , ProgramDef ):
            if self.has_service(service):
                self.programs.remove(service)
                del self.programsByUrl[service.url]
                self.serversByName[service.server.name].programs.remove(service)
                del self.serversByName[service.server.name].\
                    programsByName[service.name]
#                if (len(service.server.services)==0):
#                    del self.serversByName[service.server.name]
#                    self.servers.remove(service.server)
        elif isinstance( service , WorkflowDef ):
            if self.has_service(service):
                self.workflows.remove(service)
                del self.workflowsByUrl[service.url]
                self.serversByName[service.server.name].workflows.remove(service)
                del self.serversByName[service.server.name].\
                    workflowsByName[service.name]
#                if (len(service.server.services)==0):
#                    del self.serversByName[service.server.name]
#                    self.servers.remove(service.server)
        elif isinstance( service , ViewerDef ):
            if self.has_service(service):
                self.viewers.remove(service)
                del self.viewersByUrl[service.url]
                self.serversByName[service.server.name].viewers.remove(service)
                del self.serversByName[service.server.name].\
                    viewersByName[service.name]
#                if (len(service.server.services)==0):
#                    del self.serversByName[service.server.name]
#                    self.servers.remove(service.server)


    def _getServerProperties(self):
        """
        @return: a dict of all deployed servers associated with their respective properties
        @rtype: { server_name :{ 'url': string , 
                                 'help': string, 
                                 'repository':string , 
                                 'jobBase': string ,
                                 'programs': []  ,
                                 'workflows' : [] ,
                                 'viewers': [] #available only for local server , }
        """
        imported_portals = _cfg.portals()
        properties = {}
        all_server_dir_path = glob( os.path.join(self.servers_path , '*' ) )
        for server_dir_path in all_server_dir_path:
            if not os.path.isdir(server_dir_path):
                continue
            else:
                server_name = os.path.basename( server_dir_path )
                properties[ server_name ] = {}
                deployed_programs_path = glob( os.path.join( server_dir_path , ProgramDef.directory_basename  ,'*.xml') )
                deployed_workflows_path = glob( os.path.join( server_dir_path , WorkflowDef.directory_basename ,'*.xml') )
                properties[ server_name ][ 'programs' ] = [ os.path.basename( p )[:-4] for p in deployed_programs_path ]
                properties[ server_name ][ 'workflows' ] = [ os.path.basename( p )[:-4] for p in deployed_workflows_path ]
                if server_name == 'local':
                    properties[ server_name ][ 'url' ]        = _cfg.cgi_url()
                    properties[ server_name ][ 'help' ]       = _cfg.mailHelp()
                    properties[ server_name ][ 'repository' ] = _cfg.repository_url()
                    deployed_viewers_path = glob(os.path.join( server_dir_path , ViewerDef.directory_basename ,"*.xml") )
                    properties[ server_name ][ 'viewers' ]    = [ os.path.basename( p )[:-4] for p in deployed_viewers_path ] 
                    properties[ server_name ][ 'jobsBase' ]   = _cfg.results_url()
                elif server_name in imported_portals:
                    properties[ server_name ][ 'url' ]        = imported_portals[ server_name ][ 'url' ]
                    properties[ server_name ][ 'help' ]       = imported_portals[ server_name ][ 'help' ]
                    properties[ server_name ][ 'repository' ] = imported_portals[ server_name ][ 'repository' ]
                    properties[ server_name ][ 'repository' ] = imported_portals[ server_name ][ 'repository' ]
                    properties[ server_name ][ 'jobsBase' ]   = "%s/jobs" %properties[ server_name ][ 'repository' ]
                else:
                    r_log.warning("the server '%s' is deployed but not appear in the configuration (skip in registry)" % server_name)
                    del properties[ server_name ]
        return properties

    def getProgramUrl(self , name , server='local'):
        #the server.repository  point to services_path 
        return "%s/services/servers/local/%s/%s.xml" %( self.serversByName[server].repository , 
                                 ProgramDef.directory_basename ,
                                 name )
    
    def getWorkflowUrl(self , name , server='local'):
        return "%s/services/servers/local/%s/%s.xml" %( self.serversByName[server].repository ,
                                 WorkflowDef.directory_basename ,
                                 name )

    def getViewerUrl(self, name ):
        return "%s/services/servers/local/%s/%s.xml" %( self.serversByName[ 'local' ].repository,
                                 ViewerDef.directory_basename , 
                                 name )
            
    def getJobPID(self, url):
        """
        @param url: the url of 
        @type url: string
        @return: the potal identifier for this (the portal id is)
        @rtype: string
        """
        server = self.getServerByJobId(url)
        jobPID = url.replace(server.jobsBase,'').lstrip('/').replace('/','.')
        if server.name != 'local':
            jobPID = server.name + '.' + jobPID
        return jobPID

    def getJobURL(self, pid):
        # if the PID is composite (i.e. it's a workflow task), only take the last part into account. 
        pid = pid.split('::').pop() 
        l = pid.split('.')
        if (len(l)==2):
            server_name = 'local'
        else:
            server_name = l[0]
            l = l[1:]
        return self.serversByName[server_name].jobsBase + '/' + '/'.join(l)

    def getViewerPath(self, name):
        return os.path.join( self.servers_path , 'local', ViewerDef.directory_basename  , name + '.xml')
    
    
    def getProgramPath(self, name, server_name ='local'):
        if server_name in self.serversByName:
            if name in self.serversByName[ server_name ].programsByName:
                return self.serversByName[ server_name ].programsByName[ name ].path
            else:
                raise KeyError , "unknown service %s for server %s " %( name , server_name )
        else:
            raise KeyError , "unknown server %s" %server_name
            
    def _computeProgramPath( self , name , server_name= 'local' ):  
        return os.path.join( self.servers_path , server_name, ProgramDef.directory_basename , name + '.xml')
      
    def _computeWorkflowPath( self , name , server_name= 'local' ):  
        return os.path.join( self.servers_path , server_name, WorkflowDef.directory_basename , name + '.xml') 
      
    def getServerByJobId(self,jobId):
        for server in self.servers:
            if jobId.startswith(server.jobsBase):
                return server


class ServiceDef(DefNode):
    """
    ServiceDef is the superclass that provides the service information to the registry
    """
    
    directory_basename = None
    
    def __init__(self, url, name=None, path=None, server=None):
        """
        @param url: the url of the definition of the program on the server where it is executed
        @type url: String
        @param name: the name of the program 
        @type name: String
        @param path: the os path to the local version of the file (local file definition or local cache of distant service)
        @type path: String
        @param server: the execution server definition
        @type server: ServerDef
        """
        DefNode.__init__(self)
        self.url = url
        self.name = name
        self.path = path
        self.server = server
        self.categories = []
        
        if (self.server.name == 'local'):
            """portal id"""
            self.pid = self.name
        else:
            self.pid = '%s.%s' % (self.server.name, self.name)
        self.disabled = False
        self.authorized = True

    def isExported(self):
        return self.server.name == 'local' and self.name in _cfg.exported_services()
    
    def __eq__(self , other ):
        return self.server.name == other.server.name and self.name == other.name 
        
class ProgramDef(ServiceDef):
    """
    ProgramDef is the class that provides the service information to the registry
    """
    type = "program"
    directory_basename = "programs"  

class WorkflowDef(ServiceDef):
    """
    WorkflowDef is the class that provides the workflow information to the registry
    """
    type = "workflow"    
    directory_basename = "workflows"  
    
    
    
class ViewerDef(ServiceDef):
    """
    ViewerDef is the class that provides the viewer information to the registry
    """
    type = "viewer"
    directory_basename = "viewers"        
   



class ServerDef(DefNode):
    """
    ServerDef is the class that provides the server information to the registry
    """

    def __init__(self, name, url, help, repository, jobsBase  ):
        """    
        @param name: the short name, as displayed for instance in the services tree menu
        @type name: String
        @param url: the url of the server (cgi-bin base url for now)
        @type url: String
        @param help: the help email contact
        @type help: String
        @param repository: the url wher to find programs, workflows, etc...
        @type repository: String
        @param jobsBase: the url of the directory that contains all of the server's jobs
        @type jobsBase: String
        """
        DefNode.__init__(self)
        self.name = name
        self.url = url
        self.help = help
        self.repository = repository
        """top-level categories"""
        self.categories = [] # top-level categories        
        """the url to revieve a job"""
        self.jobsBase = jobsBase
        """ """
        self.programs = [] 
        """ """
        self.programsByName = {}
        """ """
        self.workflows = [] 
        """ """
        self.workflowsByName = {}
        self.viewers = []
        self.viewersByName = {}
        self.path = os.path.join( _cfg.services_path() , self.name )

    def __cmp__(self, other):
        """
        Comparison operator that allows to classify the servers alphabetically
        based on node names, except local server which is first
        @param other: the other node to which self is compared
        @type other: DefNode
        @return: the comparison result
        @rtype: boolean
        """
        if self.name=='local':
            return -1
        else:
            return cmp(self.name.lower(), other.name.lower())
        r_log.error(self.name)

class CategoryDef(DefNode):
    """
    CategoryDef is the class that provides the category information to the registry
    """

    def __init__ (self, name, parentCategory=None, server=None):
        """    
        @param name: the name of the category
        @type name: String
        @param parentCategory: the parent category (if any)
        @type parentCategory: CategoryDef
        @param server: the server to which the Category belongs
        @type server: ServerDef
        """
        DefNode.__init__(self)
        self.name = name
        self.parentCategory = parentCategory
        self.server = server
        self.services = [] # top-level services
        self.categories = [] # top-level categories

class ServiceTypeDef(CategoryDef):
    pass
        
registry = Registry()
registry.load()

