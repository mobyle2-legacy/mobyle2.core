########################################################################################
#                                                                                      #
#   Author: Herve Menager,                                                             #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################
from Mobyle.Workflow import Workflow, Task, Link, Parameter, Type, Datatype, Biotype, Parser  #@UnusedImport

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
    t2 = Task()
    t2.id = 2
    t2.service = 'protdist'
    t2.suspend = True
    t2.description = "Run a protdist"

    input = Parameter()
    input.id = '1'
    input.name = 'sequences'
    input.prompt = 'Input sequences'
    input.type = Type()
    input.type.datatype = Datatype()
    input.type.datatype.class_name = "Sequence"
    input.type.biotypes = [Biotype("Protein")]

    output_format = Parameter()
    output_format.id = '2'
    output_format.name = 'alignment_format'
    output_format.prompt = 'Alignment format'
    output_format.type = Type()
    output_format.type.datatype = Datatype()
    output_format.type.datatype.class_name = "String"
    
    output = Parameter()
    output.id = '3'
    output.isout = True
    output.name = 'matrix'
    output.prompt = 'Distance matrix'
    output.type = Type()
    output.type.datatype = Datatype()
    output.type.datatype.class_name = "Matrix"
    output.type.datatype.superclass_name = "AbstractText"
    output.type.biotypes = [Biotype("Protein")]
    
    l1 = Link()
    l1.to_task = t1.id
    l1.from_parameter = "1"
    l1.to_parameter = "infile"

    l2 = Link()
    l2.to_task = t1.id
    l2.from_parameter = "2"
    l2.to_parameter = "outputformat"
    
    l3 = Link()
    l3.from_task = t1.id
    l3.to_task = t2.id
    l3.from_parameter = "aligfile"
    l3.to_parameter = "infile"
    
    l4 = Link()
    l4.from_task = t2.id
    l4.from_parameter = "outfile"
    l4.to_parameter = "3"
    
    wf.tasks = [t1, t2]
    wf.links = [l1, l2, l3, l4]
    wf.parameters = [input, output_format, output]

    mp = Parser()
    
    print mp.tostring(wf)
    
    wffile = open( '/tmp/workflow.xml', 'w' )
    wffile.write( mp.tostring(wf)) 
    wffile.close()


    print mp.parse('/tmp/workflow.xml')