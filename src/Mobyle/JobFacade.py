########################################################################################
#                                                                                      #
#   Author: Herve Menager                                                              #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################
"""
Mobyle.JobFacade

This module provides an simplified and seamless access to
 - local jobs and
 - remote jobs
"""
import os
import time #@UnresolvedImport
import urllib #@UnresolvedImport
import urllib2 #@UnresolvedImport
import simplejson #@UnresolvedImport
from logging import getLogger#@UnresolvedImport
j_log = getLogger(__name__)
acc_log = getLogger('Mobyle.access')

from Mobyle.MobyleJob  import MobyleJob
from  Mobyle.Parser import parseService
from Mobyle.JobState import JobState
from Mobyle.MobyleError import MobyleError, UserValueError
from Mobyle.Registry import registry
from Mobyle.WorkflowJob import WorkflowJob
from Mobyle.Workflow import Workflow, Parser
from Mobyle.Service import Program
from Mobyle.Utils import getStatus as utils_getStatus , killJob as utils_killJob
from Mobyle.Status import Status
from Mobyle.DataProvider import DataProvider

from Mobyle.ConfigManager import Config
_cfg = Config()


class JobFacade(object):
    """
    JobFacade is an abstract class that is an access point to a Mobyle Job.
    """

    def __init__(self, programUrl=None, workflowUrl=None, service=None, jobId=None,workflowId=None):
        if programUrl is not None:
            self.programUrl = programUrl
        elif workflowUrl is not None:
            self.workflowUrl = workflowUrl            
        elif service is not None:
            self.service = service
        if jobId:
            self.jobId = jobId
        self.workflowId = workflowId

    def addJobToSession(self, session, jobInfo):
        """
        links the job to a session by:
         - adding the job to the session
         - adding the inFile data to the session
         - getting user file name from the session
        @param session: the user "session"
        @type session: Mobyle.Session
        @param jobInfo: a dictionary containing job information such as id, date, etc.
        @type: dictionary
        """
        dataUsed = []
        for param in [param for param in self.params.values() \
                      if (param.has_key('parameter') \
                      and param['parameter'].isInfile())]:
            if param['srcFileName'] and not(param['value']):
                param['userName'] = session.getData(param['srcFileName'])['userName']
                dataUsed.append(param['srcFileName'])
            if param['value'] and not(param['srcFileName']):
                param['srcFileName'] = \
                session.addData( param['userName'], \
                                  param['parameter'].getType(), \
                                  content = param['value'], \
                                  inputModes = [param['inputMode']])
                dataUsed.append(param['srcFileName'])
        session.addJob( jobInfo['id'],dataUsed=dataUsed)

    def _processForm(self):
        """
        process the cgi form:
         - preprocessing infiles, parsing user and safe file names
         - preprocessing boolean values, which have specific default values
         - create a parameter values dictionary which is used later
        """
        for paramName in self.service.getUserInputParameterByArgpos():
            param = self.service.getParameter(paramName)
            inputName = paramName 
            value, userName, src, srcFileName, inputMode = None, None, None, None, None
            if param.isInfile():
                inputMode = self.request.get(inputName+'.mode',"upload")
                if self.request.has_key(inputName+".ref"):
                    srcFileName = self.request.get(inputName+".ref")
                    src = self.session
                    userName = self.request.get(inputName+".name")
                elif self.request.has_key(inputName+".src"):
                    srcFileName = self.request.get(inputName+".srcFileName")
                    src = self.request.get(inputName+".src")
                    userName = self.request.get(inputName+".name")
                else:
                    #value = self.request.get(inputName+"_data")
                    value = self.request.get(inputName)
                    userName = paramName + ".data"
            else:
                value = self.request.get(inputName, None) 
            if value is not None or srcFileName: # if the value is not null...
                self.params[paramName] = {'value': value, 
                                          'userName': userName , 
                                          'srcFileName': srcFileName, 
                                          'src': src, 
                                          'inputMode':  inputMode, 
                                          'parameter': param
                                          }

    def parseService(self):
        """
        initializes the self.service and self.servicePID properties corresponding to the service url
          uses self.programUrl or self.workflowUrl
        """
        if hasattr(self,'programUrl'):
            self.service  = parseService(self.programUrl)
            self.servicePID = registry.programsByUrl[self.programUrl].pid
        elif hasattr(self,'workflowUrl'):
            mp = Parser()
            self.service = mp.parse(self.workflowUrl)
            self.service.url = self.workflowUrl
            self.servicePID = registry.workflowsByUrl[ self.workflowUrl ].pid   
  
    def create(self, request_fs=None, request_dict=None, session=None):
        """
        create sets up most of the class attributes TODO: check if this could be done in __init__?
        """
        self.request = {}
        if request_dict:
            self.request = request_dict
        elif request_fs:
            for key in request_fs.keys():
                self.request[key] = request_fs.getvalue(key)
        self.email = self.request.get('email', None)
        if not(self.email) and session:
            self.email = session.getEmail()
        self.parseService()
        if ( not( self.email ) and not( _cfg.opt_email( self.servicePID ) ) ):
            return {"emailNeeded":"true"}
        if (session and not(session.isActivated())):
            return {"activationNeeded":"true"}                
        self.params = {}
        self.session = session
        self._processForm()
        resp = self.submit(session)
        if resp.has_key('id'):
            self.jobId = resp['id']
            resp['pid'] = str(registry.getJobPID(resp['id']))
        # log the job in the access log
        if not(resp.has_key('errormsg')):
            msg = "%s %s %s %s %s" % (self.servicePID, # service PID
                                              resp.get('pid','').replace(self.servicePID+'.',''), #job key
                                              str(self.email), # user email
                                              os.environ.get('REMOTE_HOST',os.environ.get('REMOTE_ADDR','local')), # ip or host
                                              os.environ.get('HTTP_X_MOBYLEPORTALNAME','unknown') # client portal
                                              )
            acc_log.info( msg )
        return resp
    
    def getOutputParameterValues(self, name):
        js = JobState(self.jobId)
        outputRefs = js.getOutput(name)
        values = []
        if outputRefs:
            for outputRef in outputRefs:
                fh = js.open(outputRef[0])
                value = ''.join( fh.readlines() )
                values.append({'value':value,'ref':self.jobId+'/'+outputRef[0],'size':outputRef[1],'fmt':outputRef[2]})
        return values

    def getOutputParameterRefs(self, name):
        js = JobState(self.jobId)
        outputRefs = js.getOutput(name)
        values = []
        if outputRefs:
            for outputRef in outputRefs:
                values.append({'src':self.jobId,'srcFileName':outputRef[0],'size':outputRef[1],'fmt':outputRef[2]})
        return values


    def getFromService(cls, programUrl=None, workflowUrl=None, service=None,workflowId=None):
        """
        create a new JobFacade from the service URL.
        @param programUrl: service URL
        @type session: string
        @return: the appropriate job facade
        @rtype: JobFacade
        """
        j=None
        if programUrl:
            if registry.programsByUrl[programUrl].server.name=='local':
                j = LocalJobFacade(programUrl=programUrl, workflowId=workflowId)
            else:
                j = RemoteJobFacade(programUrl=programUrl, workflowId=workflowId)
        elif workflowUrl:
            if registry.workflowsByUrl[workflowUrl].server.name=='local':
                j = LocalJobFacade(workflowUrl=workflowUrl, workflowId=workflowId)
            else:
                j = RemoteJobFacade(workflowUrl=workflowUrl, workflowId=workflowId)
        elif service is not None:
            j = LocalJobFacade(service=service, workflowId=workflowId)
        return j
    getFromService = classmethod(getFromService)
      
    def getFromJobId(cls, jobId):
        """
        create a JobFacade to access an existing job.
        @param jobId: the job identifier
        @type jobId: string
        @return: the appropriate job facade
        @rtype: JobFacade
        """
        jobState = JobState(jobId)
        jfargs = {'jobId': jobState.getID(),'programUrl':None,'workflowUrl':None}
        if jobState.isWorkflow():
            jfargs['workflowUrl'] = jobState.getName()
        else:
            jfargs['programUrl']= jobState.getName()
        # this id is identical to the one in parameter, 
        # except it has been normalized (may have removed
        # trailing index.xml from the id)
        if jobState.isLocal():
            return(LocalJobFacade(**jfargs))
        else:
            return(RemoteJobFacade(**jfargs))
    getFromJobId = classmethod(getFromJobId)

class RemoteJobFacade(JobFacade):
    """
    RemoteJobFacade is a class that is an access point to a Mobyle Job on a remote server.
    """
    
    def __init__(self, programUrl=None, workflowUrl=None, service=None, jobId=None ,workflowId=None ):
        JobFacade.__init__(self,programUrl=programUrl, workflowUrl= workflowUrl, service=service, jobId=jobId ,workflowId = workflowId )
        if hasattr(self,'programUrl'):
            self.server = registry.programsByUrl[self.programUrl].server
        else:
            self.server = registry.workflowsByUrl[self.workflowUrl].server
        self.endpoint = self.server.url

    def submit(self, session=None):
        """
        submits the job on the remote server
        @param session: the session used to load infile values
        @type session: Mobyle.Session
        @return: job information as a dictionary
        @rtype: dictionary
        """
        endpointUrl = self.endpoint + "/job_submit.py"
        #values = self.request
        for param in [param for param in self.params.values() \
                      if (param.has_key('parameter') \
                          and param['parameter'].isInfile())]:
#            if param['srcFileName'] and not(param['value']):
#                param['value'] = session.getContentData(param['srcFileName'], \
#                                                        forceFull = True)[1]
            if param['srcFileName'] and not(param['value']):
                param['src'] = DataProvider.get(param['src'])
                param['value'] = urllib.urlopen('%s/%s' % (param['src'].getDir(), param['srcFileName'])).read()
                #param['value'] = urllib.urlopen(param['src']+'/'+param['srcFileName']).read()
        requestDict = {}
        if hasattr(self, 'programUrl'):
            requestDict['programName'] = self.programUrl
        else:
            requestDict['workflowUrl'] = self.workflowUrl            
        if self.email:
            requestDict['email'] = self.email
        requestDict['workflowId'] = self.workflowId            
        for name, param in self.params.items():
            requestDict[name] = param['value']
        try:
            response = self._remoteRequest(endpointUrl, requestDict)
        except:
            return {"errormsg":"A communication error happened during the \
                    submission of your job to the remote Portal"}
        return response
  
  
    def getStatus(self):
        """
        gets the job status on the remote server
        @return: job status information as a dictionary
        @rtype: dictionary
        """
        endpointUrl = self.endpoint + "/job_status.py"
        requestDict = {}
        requestDict['jobId'] = self.jobId
        try:
            response = self._remoteRequest(endpointUrl, requestDict)
        except:
            return {"errormsg":"A communication error happened while \
                    asking job status to the remote Portal"}
        status = Status(string=response['status'], message=response['msg'])
        return status

    def getSubJobs(self):
        """
        gets the list of subjobs (along with their status)
        @return: subjobs list of dictionaries
        @rtype: dictionary
        """
        endpointUrl = self.endpoint + "/job_subjobs.py"
        requestDict = {}
        requestDict['jobId'] = self.jobId
        response = self._remoteRequest(endpointUrl, requestDict)
        rv= []
        if response:
            for job_entry in response:
                if job_entry.has_key('jobSortDate'):
                    jobDate = time.strptime(job_entry['jobSortDate'],"%Y%m%d%H%M%S")
                if job_entry.has_key('status'):
                    jobstatus = Status(string=job_entry['status'], message=job_entry.get('status_message'))
                jobID = job_entry['url']
                jobPID = self.server.name + '.' + job_entry['jobID']
                serviceName = job_entry['programName']
                rv.append({'jobID':jobID,
                                'jobPID':jobPID,
                                'userName':jobID,
                                'programName':serviceName,
                                'date':jobDate,
                                'status':jobstatus,
                                'owner':registry.getJobPID(self.jobId)
                                })
        return rv

    def killJob(self):
        endpointUrl = self.endpoint + "/job_kill.py"
        requestDict = {}
        requestDict['jobId'] = self.jobId
        try:
            response = self._remoteRequest(endpointUrl, requestDict)
        except:
            return {"errormsg":"A communication error happened while \
                    asking job status to the remote Portal"}
        return response
    
    
    def _remoteRequest(self, url, requestDict):
        """
        encodes and executes the proper request on the remote server, with 
        proper error logging
        @param url: the target url
        @type url: string
        @param requestDict: the request parameters
        @type requestDict: dictionary
        @return: response as a dictionary
        @rtype: dictionary
        """
        data = urllib.urlencode(requestDict)
        headers = { 'User-Agent' : 'Mobyle-1.0',
                    'X-MobylePortalName' : _cfg.portal_name() }
        req = urllib2.Request(url, data,headers)
        try:
            handle = urllib2.urlopen(req)
        except (urllib2.HTTPError), e:
            j_log.error("Error during remote job communication for remote service %s \
             to %s, HTTP response code = %s" % (self.programUrl, url, e.code))
            return None
        except (urllib2.URLError), e:
            j_log.error("Error during remote job communication for remote service %s \
             to %s, URL problem = %s" % (self.programUrl, url, e.reason))
            return None
        try:
            str = handle.read()
            jsonMap = simplejson.loads(str)
        except ValueError, e:
            j_log.error("Error during remote job communication for remote service %s \
             to %s, bad response format: %s" % (self.programUrl, url, str(e)))
            return None
        return jsonMap
        

class LocalJobFacade(JobFacade):
    """
    LocalJobFacade is a class that is an access point to a Mobyle Job on the local server.
    """


    def submit(self, session=None):
        """
        submits the job on the local server
        @param session: the session used to load infile values
        @type session: Mobyle.Session
        @return: job information as a dictionary
        @rtype: dictionary
        """
        try:
            if isinstance(self.service, Program):
                self.job = MobyleJob( service    = self.service , 
                                      email      = self.email,
                                      session    = session,
                                      workflowID = self.workflowId)
            elif isinstance(self.service, Workflow):
                self.job = WorkflowJob( workflow   = self.service,
                                        email      = self.email,
                                        session    = session,
                                        workflowID = self.workflowId)
            else:
                raise NotImplementedError("No Job can be instanciated for a %s service" % str(self.service.__class__))
            for name, param in self.params.items():
                if param['parameter'].isInfile():
                    if param['src']:
                        param['src'] = DataProvider.get(param['src'])
                        self.job.setValue(name, (param['userName'], None, param['src'], param['srcFileName']))      
                    else:
                        self.job.setValue(name, (param['userName'], param['value'], None, None))      
                else:
                    if param['parameter'].getDataType().getName() == 'MultipleChoice': 
                        from types import StringTypes
                        if isinstance(  param['value'] , StringTypes ):
                            param['value'] = [ param['value'] ]
                    self.job.setValue(name, param['value'])
            # run Job
            self.job.run()
            return {
                    'id': str(self.job.getJobid()),
                    'date':str(time.strftime( "%x  %X", self.job.getDate())),
                    'status': str( self.job.getStatus() ),
                    }
        except UserValueError, e:
            if hasattr(e, 'message') and e.message:
                msg = {'errormsg':str(e.message)}
            else:
                msg = {'errormsg':str(e)}
            if hasattr(self, 'job') and self.job:
                jobId = self.job.getJobid()
                msg['id'] = str(jobId)
            if hasattr(e, 'param') and e.param:
                msg["errorparam"] = e.param.getName()
            if jobId:
                pid_str = str(registry.getJobPID(jobId))
            else:
                pid_str = "none"
            j_log.error("user error in job %s (email %s): %s"% (pid_str, getattr(self,"email","anonymous"),str(e)))
            return msg
        except MobyleError, e:
            j_log.error(e, exc_info = True)
            if hasattr(e, 'message') and e.message:
                msg = {'errormsg':str(e.message)}
            else:
                msg = {'errormsg':str(e)}
            if hasattr(self, 'job') and self.job:
                jobId = self.job.getJobid()
                msg['id'] = str(jobId)
            if hasattr(e, 'param') and e.param:
                msg["errorparam"] = e.param.getName()
            return msg
  
  
    def getStatus(self):
        """
        gets the job status on the local server
        @return: job status information as a dictionary
        @rtype: dictionary
        """
        return utils_getStatus( self.jobId )
    
    def getSubJobs(self):
        """
        gets the list of subjobs (along with their status)
        @return: subjobs list of dictionaries
        @rtype: list
        """
        js = JobState(self.jobId)
        if hasattr(js, 'getSubJobs'):
            subjobs = js.getSubJobs()
            subsubjobs = []
            for s in subjobs:
                s['jobPID'] = registry.getJobPID(self.jobId) + '::'+ registry.getJobPID(s['jobID'])
                child_jf = JobFacade.getFromJobId(s['jobID'])
                s['status'] = child_jf.getStatus()
                for ss in child_jf.getSubJobs():
                    ss['jobPID'] = s['jobPID'] + '::' + registry.getJobPID(ss['jobID'])
                    schild_jf = JobFacade.getFromJobId(ss['jobID'])
                    ss['status'] = schild_jf.getStatus() 
                    subsubjobs.append(ss)                   
            subjobs.extend(subsubjobs)
            return subjobs
        else:
            return []

        
    def killJob(self):
        """
        
        """
        utils_killJob( self.jobId )