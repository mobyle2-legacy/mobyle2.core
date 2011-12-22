########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################



class Dispatcher( object ):
    """choose the right ExecutionSystem and queue for a program"""
    
    def _getJobNameFromJobState(self , jobState ):
        job_name = jobState.getName().split( '/' )[-1]
        job_name = job_name[:-4]
        return job_name
    
    def getQueue(self , jobState ):
        """
        @param jobState: the jobState of a job
        @type jobState: a MobyleJobState instance
        @return: the queue for this job
        @rtype: string
        """
        raise NotImplementedError( "you must redefined getQueue method in your subclass")
    
    def getExecutionConfig(self , jobState ):
        """
        @param jobState: the jobState of a job
        @type jobState: a MobyleJobState instance
        @return: the execution system to use to launch this job
        @rtype: ExecutionSystem instance
        """
        raise NotImplementedError( "you must redefined getExecutionConfig method in your subclass")
    
    
    
class DefaultDispatcher( Dispatcher ):
    
    
    def __init__(self, routes ):
        """
        @param routes: represent all execution system and queue associated to each programs name
        @type routes: dict which keys are the names of programs and values a tuple
        the first value of the tuple is an EXECUTION_SYSTEM_ALIAS entry and the 2nde value a queu name
        routes = { string program name : (  ExecutionConfig object from EXECUTION_SYSTEM_ALIAS , string queue name ) , ...}
        """
        self.routes = routes
    
    def getExecutionConfig(self , jobState ):
        """
        @param jobState: the jobState of a job
        @type jobState: a MobyleJobState instance
        @return: the execution config need to launch this job
        @rtype: ExecutionConfig instance
        """
        job_name = self._getJobNameFromJobState( jobState )
        if job_name in self.routes:
            exec_sys = self.routes[ job_name ][0] 
        else:
            exec_sys = self.routes[ 'DEFAULT' ][0]
        return exec_sys
        
    def getQueue(self , jobState ):
        """
        @param jobState: the jobState of a job
        @type jobState: a MobyleJobState instance
        @return: the queue for this job
        @rtype: string
        """
        job_name = self._getJobNameFromJobState( jobState )
        if job_name in self.routes:
            queue = self.routes[ job_name ][1] 
        else:
            queue = self.routes[ 'DEFAULT' ][1]
        
        return queue
    
    def routes(self):
        """
        @return: all routes for this configuration
        @rtype: list of tuples ( ExecutionSystem instance , queue )
        """
        return self.routes.keys()