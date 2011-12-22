########################################################################################
#                                                                                      #
#   Author: Herve Menager,                                                             #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################
from Mobyle.Workflow import Parser
from Mobyle.WorkflowJob import WorkflowJob

if __name__ == "__main__":
    
    mp = Parser()
    #wf = mp.parse('/tmp/workflow.xml') # 1st example
    wf = mp.parse('/tmp/workflow2.xml') # 2nd example
    class SessionFake(object):
        def getKey(self):
            return "workflowjobdemotestmodule"
    wf.owner = SessionFake()

    parameters = {'sequences': """>A
TTTT

>B
TATA""",
    'alignment_format': 'PHYLIP'}
    
    wj = WorkflowJob(workflow=wf,email='hmenager@pasteur.fr')
    print wj.id
    #for key, value in parameters.items(): # set values for 1st example
    #    wj.set_value(key, value)
    wj.srun() #synchronous calls
    #wj.run #asynchronous calls