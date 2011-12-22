########################################################################################
#                                                                                      #
#   Author: Herve Menager,                                                             #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################
from Mobyle.Workflow import Parser

if __name__ == "__main__":

    mp = Parser()
    wf = mp.parse('/tmp/workflow.xml')
    class SessionFake(object):
        def getKey(self):
            return "workflowjobdemotestmodule"
    wf.owner = SessionFake()

    parameters = {'sequences': """>A
TTTT

>B
TATA""",
    'alignment_format': 'PHYLIP',
    'email': 'hmenager@pasteur.fr'}

    import Mobyle.JobFacade
    wj = Mobyle.JobFacade.JobFacade.getFromService(service=wf)
    print wj.create(request_dict=parameters)