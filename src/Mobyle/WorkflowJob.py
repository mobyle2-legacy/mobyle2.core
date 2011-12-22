########################################################################################
#                                                                                      #
#   Author: Herve Menager,                                                             #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################
import time #@UnresolvedImport
import os, sys
import signal
import logging #@UnresolvedImport
import atexit #@UnresolvedImport

from Mobyle.Job import Job
from Mobyle.Registry import registry
from Mobyle import ConfigManager
from Mobyle.JobState import JobState
from Mobyle.Service import MobyleType, Parameter
from Mobyle.Classes.DataType import DataTypeFactory
from Mobyle.DataProvider import DataProvider
from Mobyle.Status import Status
from Mobyle.StatusManager import StatusManager
from Utils import zipFiles , emailResults
from Mobyle.MobyleError import MobyleError, UserValueError
from Mobyle.Net import EmailAddress
import Mobyle

log = logging.getLogger(__name__)

##to have all debug logs
#log.setLevel( logging.DEBUG )

##to have only synchronization father<->child process debug logs
##don't forget to turn on log in RunnerChild (in atexit)
#log.setLevel( 12 )

##to block debug logs 
log.setLevel( logging.INFO )


class WorkflowJob(object):
    
    def __init__(self, id=None, workflow=None, email=None, email_notify = 'auto', session=None, workflowID = None):
        """
        @param id: the identifier of this workflow (it's used to rebuild WorkflowJob using it's id)
        @type id: string 
        @param workflow: the workflow definition used to create a new job
        @type workflow: a L{Workflow} instance
        @param email: the user email address
        @type email: L{EmailAddress} instance or a string
        @param email_notify: if the user must be or not notify of the results at the end of the Job.
        the 3 authorized values for this argument are: 
          - 'true' to notify the results to the user
          - 'false' to Not notify the results to the user
          - 'auto' to notify the results based on the job elapsed time and the config  EMAIL_DELAY
        @type email_notify: string 
        @param session: the session owner of this workflow (if session is set workflowID mut be None )
        @type session: a L{Session} instance
        @param workflowID: the ID of a the workflow owner of this workflow
        @type workflowID: string
        """
        self.cfg = ConfigManager.Config()
        self.status_manager = StatusManager()
        if id:
            log.debug("accessing WorkflowJob %s" %(id))
            self.id = id
            self.jobState = JobState( id )
        else:
            log.debug("creating WorkflowJob for workflow '%s'" %(workflow.name))
            self.workflow = workflow
            if session and workflowID:
                msg = "try to instanciate a workflow with 2 owners: session %s & workflowID %s" %( session.getKey(),
                                                                                                   workflowID
                                                                                                  )
                log.error( msg )
                raise MobyleError( msg )
            self.session = session
            if session :
                email = session.getEmail()
                if email:
                    self.email = EmailAddress( email )
                else:
                    self.email = None
            elif email : #there is an email without session
                if  not isinstance( email , EmailAddress ):
                    self.email = EmailAddress( email )
                else:
                    self.email = email
            
            self.email_notify =  email_notify  
            if self.email_notify != 'false' and not self.email:
                raise MobyleError( "email adress must be specified when email_notify is set to %s" % email_notify )
            
            self.parameters = {}
            for parameter in self.workflow.parameters:
                # setting parameters which have a default value (important for hidden parameters which are not 
                # accessed by JobFacade...
                if not(parameter.isout) and parameter.vdef is not None:
                    self.set_value(parameter.name, value=str(parameter.vdef))
            # job is just an "environment" folder for the job
            # it contains the instanciation of the job runner which seems to be hardcoded as "command runner"...
            self._job = Job( service = self.workflow,
                             cfg = self.cfg,
                             userEmail = self.email,
                             session = self.session,
                             workflowID = workflowID ,
                             )
            self.jobState = self._job.jobState
            self.id = self._job.getURL()
            
    def getDir(self):        
        """ returns the absolute path of the workflow job directory """
        return self.jobState.getDir()
    
    def set_status(self, status):
        log.debug("setting job %s status to %s" % (self.id, status))
        self.status_manager.setStatus( self.getDir() , status )
        
    def set_value(self, parameter_name, value=None, src=None, srcFileName=None):
        wf_parameter = [p for p in self.workflow.parameters if p.name==parameter_name][0]
        if value is not None:
            log.debug("setting %s parameter value to %s" %(parameter_name, value))
        elif src is not None:
            log.debug("copying %s parameter value from %s/%s" %(parameter_name, src,srcFileName))
        else:
            log.error("no VALUE or SOURCE URL specified for %s parameter." % parameter_name)            
        """ set a parameter value """
        self.parameters[parameter_name] = value
        self.parameters[parameter_name + '.src'] = src
        self.parameters[parameter_name + '.srcFileName'] = srcFileName
        if value and value==wf_parameter.vdef:
            log.debug("setting %s parameter value to default value %s" %(parameter_name, wf_parameter.vdef))
            return            
        # save input value in a file
        # link this file from the JobState xml
        datatype_class = wf_parameter.type.datatype.class_name
        datatype_superclass = wf_parameter.type.datatype.superclass_name
        df = DataTypeFactory()
        if (datatype_superclass in [None,""] ):
            dt = df.newDataType(datatype_class)
        else:
            dt = df.newDataType(datatype_superclass, datatype_class)
        mt = MobyleType(dt)
        p = Parameter(mt, name=parameter_name)
        p._isout = wf_parameter.isout
        if dt.isFile():
            file_name = parameter_name+'.data'
            if src:
                src = DataProvider.get(src)
            file_name, size = mt.toFile( value , self , file_name, src , srcFileName  )
            if not(wf_parameter.isout):
                self.jobState.setInputDataFile(parameter_name, (file_name, size, None))
            else:
                self.jobState.setOutputDataFile(parameter_name, [(file_name, size, None)])
        else:
            if not(wf_parameter.isout):            
                self.jobState.setInputDataValue(parameter_name, value)
            else:
                raise NotImplementedError() # so far Mobyle does not manage non-file outputs
        self.jobState.commit()
    
    def setValue(self, parameter_name, value=None, src=None, srcFileName=None):
        """MobyleJob-style set value method, called from JobFacade"""
        if type(value)==tuple:
            return self.set_value(parameter_name, value=value[1], src=value[2],srcFileName=value[3])
        else:
            return self.set_value(parameter_name, value=value, src=src,srcFileName=srcFileName)
        
    def getJobid(self):
        """MobyleJob-style get job id method, called from JobFacade"""
        return self.id

    def getDate(self):
        """MobyleJob-style get date method, called from JobFacade"""
        return time.strptime(self.get_date(),"%x  %X")
    
    def getStatus(self):
        """MobyleJob-style get status method, called from JobFacade"""
        return self.status_manager.getStatus( self.getDir() )
            
    def get_value(self, parameter_name):
        """get a parameter value"""
        return self.parameters.get(parameter_name,None)

    def get_date(self):
        """get the job date as a string"""
        return self.jobState.getDate()

    def get_id(self):
        """get the job id"""
        return self.id
    
    def run(self):
        """submit the job asynchronously"""
        self.validate()
        self.set_status(Status( code = 1 )) # status = submitted
        
        #raise a UserValueError if nb of job is over the limit accepted
        if( self.email is not None ):
            self._job.over_limit( self.email , '' )
        
        self._child_pid = os.fork()
        if self._child_pid==0:
            #Child code
            os.setsid()
            log_fd = os.open("%s/log" % self.jobState.getDir(), os.O_APPEND | os.O_WRONLY | os.O_CREAT , 0664 )  
            devnull = os.open( "/dev/null" , os.O_RDWR )
            os.dup2( devnull , sys.stdin.fileno() )
            os.close( devnull)
            os.dup2( log_fd  , sys.stdout.fileno() )
            os.dup2( log_fd  , sys.stderr.fileno() )
            os.close( log_fd )
            atexit.register( self.log , "child exit for workflow id: %s" % self.get_id())
            
            ################################################
            service = self._job.getService()
            serviceName = service.getName()
            jobKey = self._job.getKey()
             
            linkName = ( "%s/%s.%s" %( self.cfg.admindir() ,
                                       serviceName ,
                                       jobKey
                                       )
                                       )
            try:
                
                os.symlink(
                           os.path.join( self.getDir() , '.admin') ,
                           linkName
                           )
            except OSError , err:
                self.set_status(Status(string="error", message="workflow execution failed"))
                msg = "can't create symbolic link %s in ADMINDIR: %s" %( linkName , err )
                log.critical( "%s/%s : %s" %( serviceName, jobKey, msg ), exc_info = True )
                raise WorkflowJobError , msg
        
            ################################################       
            t0 = time.time()
            self.srun()
            t1 = time.time()
            ################################################
            try:
                os.unlink( linkName )
            except OSError , err:
                self.set_status(Status(string="error", message="workflow execution failed"))
                msg = "can't remove symbolic link %s in ADMINDIR: %s" %( linkName , err )
                log.critical( "%s/%s : %s" %( serviceName, jobKey, msg ), exc_info= True )
                raise WorkflowJobError , msg
            ################################################
            try:
                zipFileName = self.zip_results()
            except Exception :
                msg = "an error occured during the zipping results :\n\n"
                log.critical( "%s : %s" %( self.id , msg ) , exc_info = True)
                zipFileName = None
                
            if self.email_notify == 'auto':
                if ( t1 - t0 ) > self.cfg.email_delay() :
                    emailResults(  self.cfg ,
                                   self.email, #userEmail, 
                                   registry, 
                                   self.id, 
                                   self.getDir(), 
                                   self.workflow.getName(),
                                   self._job.getKey(),  
                                   FileName = zipFileName )
                elif self.email_notify == 'true':
                    emailResults(  self.cfg ,
                                   self.email, #userEmail, 
                                   registry, 
                                   self.id, 
                                   self.getDir(), 
                                   self.workflow.getName(),
                                   self._job.getKey(),  
                                   FileName = zipFileName )
                else:
                    pass    
            sys.exit(0) #exit with no error
        else:
            #return properly to the cgi
            return
        
    def zip_results(self):
        
        job_dir = self.getDir()
        files2zip = []
       
        input_files = self.jobState.getInputFiles() #inputFiles = [ ( parameterName , [ (fileName , format or None ) , ...) , ... ]
        if input_files is not None:
            for files in input_files:
                for item in files[1]: #item = ( filename , size , fmt ) 
                    files2zip.append( ( os.path.join( job_dir , item[0] ) , item[0] ))
                    
        output_files = self.jobState.getOutputs() #inputFiles = [ ( parameterName , [ (fileName , format or None ) , ...) , ... ]
        if output_files is not None:
            for files in output_files:
                for item in files[1]: #item = ( filename , size  ) 
                    files2zip.append( ( os.path.join( job_dir , item[0] ) , item[0] ) ) 
        
        files2zip.append( ( os.path.join( job_dir , "index.xml") , "index.xml" ) )

        xsl_path = os.path.join( self.cfg.portal_path() , "xsl" ,)
        jobXslPath = os.path.join( xsl_path , "job.xsl" ) 
        files2zip.append( ( jobXslPath , "job.xsl" ) )
        cssPath = os.path.join( self.cfg.portal_path() , "css",  "mobyle.css" ) 
        files2zip.append( ( cssPath , "mobyle.css" ) )
                
        identXslPath = os.path.join( xsl_path , "ident.xsl" )
        files2zip.append( ( identXslPath , "ident.xsl" ) )
        
        zipFileName = "%s_%s.zip" %( self.workflow.getName() , self._job.getKey() )
        zipFileName = os.path.join( job_dir , zipFileName )
        zip_filename = zipFiles( zipFileName , files2zip ) 
        return  zip_filename
                
    def log(self, message):
        print >>sys.stderr , message        
    
    def srun(self):
        """run the job synchronously"""
        try:
            self._prepare()
            self._debug_state()
            self.set_status(Status( code = 3 )) # status = running
            # run while no error status
            # and output parameters do not have a value
            signal.signal( signal.SIGALRM , self.alarm_handler )
            while True :
                signal.alarm( 30 )
                status = self.status_manager.getStatus( self.getDir() )
                if status.isOnError() and status.code==6:#killed
                    self._kill_subjobs()
                    break
                else:  
                    self._iterate_processing()
                if len([j for j in self.sub_jobs if (not(j.has_key('job_status')) or not(j['job_status'].isEnded()))])==0:
                    # workflow is considered to be finished when all the tasks have completed
                    log.log( 12 , "all tasks completed." )
                    self.log("all tasks completed.")
                    break
                try:
                    pid = os.wait()
                except OSError , err :
                    if err.errno == 10 :
                        log.log( 12 , "no more local child process, maybe remote jobs exist -> continue" )
                        time.sleep(30)
                        continue
                    elif err.errno == 4 :
                        log.log( 12 , "interrupt by a system call ( SIGALRM ? ), continue  err = %s time = %f "%( err , time.time() ) )
                        continue
                    else:
                        log.log( 12 , "unexpected error, err = %s  time = %f -> break"%( err, time.time() ) , exc_info = True )
                        break
                log.log( 12, "end of loop at %f pid, returncode = %s" %(time.time(), pid ) )
            signal.alarm(0)
            self._finalize()
            log.debug("job processing ending for job %s, status %s" % (self.get_id(), self.status_manager.getStatus( self.getDir() )))
            self._debug_state()
        except WorkflowJobError, we:
            # if an "known" runtime error occurs
            self.set_status(Status(string='error', message=we.message))
        except Exception:
            # if an unspecified runtime error occurs
            self.set_status(Status(string="error",message="workflow execution failed"))
            log.error("Error while running workflow job %s" % self.id, exc_info=True)
    
    def alarm_handler( self, signum ,frame ):
        """
        @call: when the a SIGALRM is raise
        """
        log.log( 12 , " %d : alarm_handler recieved a signal %d "% (os.getpid() , signum) )
        pass
        
        
    def _prepare(self):
        """prepare for executions"""
        self.sub_jobs = []
        for t in self.workflow.tasks:
            self.sub_jobs.append({'task':t})
        # build data transfers scheduling self.data
        self.data = []
        for p in self.workflow.parameters:
            # for each task that has to be run, check if an input is expected, and if expected,
            # check if this input is already "valued"
            # TODO at workflow validation time, we should check for each parameter of a service if a parameter
            # is mandatory and if so if it is linked to a default value or a link
            log.debug('preparing parameter %s' % p)
            if(not(bool(p.isout))):
                self.data.append({'type':'input','parameter':p})
            else:
                self.data.append({'type':'output','parameter':p})
        for t in self.workflow.tasks:
            # for each task that has to be run, check if an input is expected, and if expected,
            # check if this input is already "valued"
            # TODO at workflow validation time, we should check for each parameter of a service if a parameter
            # is mandatory and if so if it is linked to a default value or a link
            log.debug('preparing task %s' % t)
            for i in [l for l in self.workflow.links if l.to_task==t.id]:
                self.data.append({'type':'task_input','task':t, 'parameter_id':i.to_parameter})
            for o in [l for l in self.workflow.links if l.from_task==t.id]:
                self.data.append({'type':'task_output','task':t, 'parameter_id':o.from_parameter})
            for iv in t.input_values:
                ti = {'type':'task_input','task':t, 'parameter_id':iv.name}
                if iv.value is not None:
                    ti['value'] = iv.value
                elif iv.reference:
                    ti['src'] = iv.reference
                self.data.append(ti)
        for l in self.workflow.links:
            log.debug('preparing link %s' % l)
            self.data.append({'type':'link','link':l})
        # setting parameter values
        for entry in [entry for entry in self.data if (entry['type']=='input' and not(entry.has_key('value') or entry.has_key('src') or entry.has_key('srcFileName')))]:
            if self.parameters.get(entry['parameter'].name):
                entry['value'] = self.parameters.get(entry['parameter'].name,None)
            else:
                entry['src'] = self.parameters.get(entry['parameter'].name+'.src',None)
                entry['srcFileName'] = self.parameters.get(entry['parameter'].name+'.srcFileName',None)

    def validate(self):
        """ check that a value is provided for each mandatory field """
        mandatory_list = [p for p in self.workflow.parameters if not(p.isout) and p.ismandatory and (p.vdef is None or p.vdef=='')]
        for p in mandatory_list:
            if not(self.parameters.get(p.name)) and not(self.parameters.get('%s.src' % p.name)):
                raise UserValueError(parameter = p, msg = "This parameter is mandatory" )            

    def _iterate_tasks(self):
        """launch and monitor task executions"""
        job_signal = False
        # starting jobs
        for t in self.workflow.tasks:
            input_entries = [entry for entry in self.data if (entry['type']=='task_input' and entry['task'].id==t.id)]
            # if data available and not already running
            if (len(input_entries)==len([entry for entry in input_entries if entry.has_key('value') or entry.has_key('srcFileName')])):
                job_entry = [job_entry for job_entry in self.sub_jobs if job_entry['task'].id==t.id][0]
                if job_entry.has_key('job_id'):
                    job_id = job_entry['job_id']
                    if not(job_entry['job_status'].isEnded()):
                        j = Mobyle.JobFacade.JobFacade.getFromJobId(job_id)
                        su_signal = self._process_subjob_status_update(j, job_entry, t)
                        job_signal = job_signal or su_signal
                else:
                    # if job is not running, start it
                    log.debug('starting job for task %s' % t.id)
                    log.debug('registry.getProgramUrl(t.service = %s,t.server= %s)' %(t.service , t.server) )
                    if t.server is None:
                        t.server = 'local'
                    job_parameters = {}
                    try:
                        url = registry.getProgramUrl(t.service,t.server)
                        j = Mobyle.JobFacade.JobFacade.getFromService(programUrl=url, workflowId=self.id)
                        job_parameters['programName'] = url
                    except:
                        url = registry.getWorkflowUrl(t.service,t.server)
                        j = Mobyle.JobFacade.JobFacade.getFromService(workflowUrl=url, workflowId=self.id)                        
                        job_parameters['workflowUrl'] = url
                    job_signal = True
                    for i_e in input_entries:
                        if i_e.has_key('value'):
                            job_parameters[i_e['parameter_id']]=i_e['value']
                        else:
                            job_parameters[i_e['parameter_id']+'.src']=i_e['src']
                            job_parameters[i_e['parameter_id']+'.srcFileName']=i_e['srcFileName']
                            job_parameters[i_e['parameter_id']+'.mode']='result'
                            job_parameters[i_e['parameter_id']+'.name']=i_e['parameter_id']+'.data'
                    job_parameters['email'] = self.email
                    try:
                        resp = j.create(request_dict=job_parameters)
                    except Exception, e:
                        raise WorkflowJobError("error during submission of task %s(%s)" \
                                                  %(t.id, t.description))
                    job_entry['job_id'] = resp['id']
                    if resp.has_key('errorparam') or resp.has_key('errormsg'):
                        raise WorkflowJobError("error during submission of task %s(%s).\n job %s message: %s: %s." \
                                                  %(t.id, t.description,job_entry['job_id'],resp.get('errorparam'),resp.get('errormsg')))
                    self.jobState.setTaskJob(t,job_entry['job_id'])
                    self.jobState.commit()
                    su_signal = self._process_subjob_status_update(j, job_entry, t)
                    job_signal = job_signal or su_signal
                    log.debug('job for task %s: %s' % (t.id, job_entry['job_id']))
        return job_signal

    def _process_subjob_status_update(self, j, job_entry, t):
        """ check a subjob status and update the workflow job status, process outputs and raise an exception if relevant """
        new_status = j.getStatus()
        if not(job_entry.has_key('job_status')) or new_status!=job_entry['job_status']:
            job_entry['job_status'] = new_status
            #update it if it changed since last check
            self.set_status(Status( code = 3 ,
                                        message="job %s: %s" % (job_entry['job_id'] , job_entry['job_status'])))             
            if new_status.isOnError():
                raise WorkflowJobError("job %s for task %s failed." %(job_entry['job_id'], t.id)) # error, so nothing to be done
            if new_status.isEnded():
                # if status complete copy job outputs to task output
                output_entries = [entry for entry in self.data if (entry['type']=='task_output' and entry['task'].id==t.id)]
                for o in output_entries:
                    output_values = j.getOutputParameterRefs(o['parameter_id'])
                    if len(output_values)>0:
                        o['src'] = output_values[0]['src'] #FIXME WE TAKE ONLY THE FIRST VALUE INTO ACCOUNT!!!
                        o['srcFileName'] = output_values[0]['srcFileName']
                    else:
                        # if the expected result has not been produced
                        raise WorkflowJobError("expected output %s has not been produced by task %s (job %s)" 
                                               %(o['parameter_id'], t.id, job_entry['job_id'])) # error, so nothing to be done
            return True # jobSignal
        else:
            return False
        
    def _iterate_data(self):
        """link data between tasks"""
        data_signal = False
        # linking data
        new_data = self.data
        for item in [item for item in self.data if item['type']=='link']:
            log.debug("processing data entry %s" % item)
            link = item['link']
            if not(link.from_task):
                log.debug("from workflow input to task input")
                source = [entry for entry in self.data if entry['type']=='input' and entry['parameter'].id==link.from_parameter][0]
                target = [entry for entry in self.data if (entry['type']=='task_input' and entry['task'].id==link.to_task and entry['parameter_id']==link.to_parameter)][0]
            elif link.to_task:
                log.debug("from task output to task input")
                source = [entry for entry in self.data if entry['type']=='task_output' and entry['task'].id==link.from_task and entry['parameter_id']==link.from_parameter][0]
                target = [entry for entry in self.data if (entry['type']=='task_input' and entry['task'].id==link.to_task and entry['parameter_id']==link.to_parameter)][0]
            else:
                log.debug("from task output to workflow output")
                source = [entry for entry in self.data if entry['type']=='task_output' and entry['task'].id==link.from_task and entry['parameter_id']==link.from_parameter][0]
                target = [output for output in self.data if output['type']=='output' and output['parameter'].id==link.to_parameter][0]
            log.debug(source)
            log.debug(target)
            if source.has_key('src') or source.has_key('value'):
                if source.has_key('src'):
                    target['src'] = source['src']
                    target['srcFileName'] = source['srcFileName']
                elif source.has_key('value'):
                    target['value'] = source['value']                    
                log.debug("processing %s" % target)
                data_signal = True
                log.debug("removing %s" % entry)
                new_data.remove(item)
        self.data = new_data
        return data_signal

    def _iterate_processing(self):
        """link data between tasks, launch and monitor task executions"""
        self._debug_state()
        ts, ds = True, True
        while (ts or ds) :
            ts = self._iterate_tasks()
            ds = self._iterate_data()
        log.debug(ts)
        log.debug(ds)

    def _finalize(self):
        """set job output values"""
        for output in [output for output in self.data if output['type']=='output' and (output.get('value') or\
                                                                                        (output.get('src') and output.get('srcFileName')))]:
            self.set_value(output['parameter'].name,output.get('value'),output.get('src'),output.get('srcFileName'))
        self.set_status(Status( code = 4 )) # status = finished
    
    def kill(self):
        status = Status( code =  6 , message ="Your job has been cancelled" )# status = killed
        self.set_status( status ) 
        
    def _kill_subjobs(self):
        for job_entry in self.sub_jobs:
            if 'job_id' in job_entry:
                job_id = job_entry['job_id']
                j = Mobyle.JobFacade.JobFacade.getFromJobId(job_id)
                if job_entry['job_status'].isQueryable():
                    try:
                        j.killJob()
                    except Exception, err:
                        log.error("workflow %s cannot kill job %s : %s" %( self.id , job_id , err) )
                        continue
                    
    def _debug_state(self):
        log.debug("workflow job %s summary" % self.id)
        log.debug("data summary:")
        for entry in self.data:
            log.debug(entry)
        log.debug("jobs summary:")
        for entry in self.sub_jobs:
            log.debug(entry)
            
class WorkflowJobError(MobyleError):
    """ WorkflowJobErrors are raised if something unexpected happens
    during the execution of a workflow """
    pass