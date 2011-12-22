########################################################################################
#                                                                                      #
#   Author: Herve Menager,                                                             #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################
import pygraphviz as pgv  #@UnresolvedImport
from logging  import getLogger#@UnresolvedImport
log = getLogger(__name__)
from copy import deepcopy

def layout(workflow, program='dot', format='svg'):
    workflow = deepcopy(workflow) # we are working on a copy of the original workflow object to be able to tweak the IDs safely
    g=pgv.AGraph(strict=False,directed=True)
    g.graph_attr['label']=workflow.title
    g.graph_attr['rankdir']='LR'
    g.graph_attr['tooltip']=workflow.title
    links = workflow.links
    parameters = workflow.parameters
    # this part
    # - removes workflow parameters which are not used in two different task inputs
    # - renames the corresponding task parameters to the prompt of the source workflow parameter 
    for link in workflow.links:
        keep_flag = (link.from_task is not None and link.to_task is not None)\
                    or\
                    (link.to_task and len([l for l in workflow.links if not(l.from_task) \
                                           and l.from_parameter==link.from_parameter ])>1)
        if not keep_flag:
            links.remove(link)
            if (link.from_parameter and not link.from_task):
                p = [param for param in workflow.parameters if link.from_parameter==param.id][0]
                link.to_parameter=p.prompt.replace('\n','').strip()
                parameters.remove(p)
            if link.to_parameter and not link.to_task:
                p = [param for param in workflow.parameters if link.to_parameter==param.id][0]
                link.from_parameter=p.prompt.replace('\n','').strip()
                parameters.remove(p)
    for task in workflow.tasks:
        inputs = '|'.join(list(set(['<%s>%s' % (link.to_parameter,link.to_parameter) for link in workflow.links if link.to_task==task.id])))
        outputs = '|'.join(list(set(['<%s>%s' % (link.from_parameter,link.from_parameter) for link in workflow.links if link.from_task==task.id])))
        label = "%(service)s|{{%(inputs)s}|%(description)s|{%(outputs)s}}" % {'service':task.service, 'description':task.description.replace('\n','').strip(), 'inputs':inputs,'outputs':outputs}
        g.add_node(task,label=label,shape='record',tooltip=task.description)
    for param in parameters:
        g.add_node(param, label=param.prompt, shape='diamond')
    for link in links:
        sp, tp = None, None
        if link.from_task:
            s = [s for s in workflow.tasks if s.id==link.from_task][0]
            sp = link.from_parameter
        else:
            s = [s for s in workflow.parameters if s.id==link.from_parameter][0]
        if link.to_task:
            t = [t for t in workflow.tasks if t.id==link.to_task][0]
            tp = link.to_parameter
        else:
            t = [t for t in workflow.parameters if t.id==link.to_parameter][0]
        if sp and tp:
            g.add_edge(g.get_node(s),g.get_node(t), headport=tp, tailport=sp)
        elif sp:
            g.add_edge(g.get_node(s),g.get_node(t), tailport=sp)            
        elif tp:
            g.add_edge(g.get_node(s),g.get_node(t), headport=tp)            
        else:
            g.add_edge(g.get_node(s),g.get_node(t))
    g.layout(prog=program)
    return g.draw(format=format)