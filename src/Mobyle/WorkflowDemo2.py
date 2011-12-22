########################################################################################
#                                                                                      #
#   Author: Herve Menager,                                                             #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################
from Mobyle.Workflow import Workflow, Task, Link, Parameter, Type, Datatype, Biotype, Parser, InputValue  #@UnusedImport

print __file__

if __name__ == "__main__":
    
    wf = Workflow()
    wf.name = 'toto'
    wf.version = '1.1'
    wf.title = 'test workflow'
    wf.description = 'this workflow is a test one'
    t1 = Task()
    t1.id = 1
    t1.service = 'clustalw-multialign'
    t1.suspend = False
    t1.description = "Run a clustalw"

    iv = InputValue()
    iv.name = 'infile'
    iv.value = """>A
TTTT

>B
TATA
"""
    iv2 = InputValue()
    iv2.name = 'outputformat'
    iv2.value = 'PHYLIP'

    t1.input_values = [iv,iv2]
    
    t2 = Task()
    t2.id = 2
    t2.service = 'protdist'
    t2.suspend = True
    t2.description = "Run a protdist"
    
    l = Link()
    l.from_task = t1.id
    l.to_task = t2.id
    l.from_parameter = "aligfile"
    l.to_parameter = "infile"
    
    wf.tasks = [t1, t2]
    wf.links = [l]

    mp = Parser()
    
    print mp.tostring(wf)
    
    wffile = open( '/tmp/workflow2.xml', 'w' )
    wffile.write( mp.tostring(wf)) 
    wffile.close()


    print mp.parse('/tmp/workflow2.xml')