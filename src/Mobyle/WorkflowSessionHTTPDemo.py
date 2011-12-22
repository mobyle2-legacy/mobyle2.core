########################################################################################
#                                                                                      #
#   Author: Herve Menager,                                                             #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

MOBYLEHOME = None

import os
import sys
if os.environ.has_key('MOBYLEHOME'):
    MOBYLEHOME = os.environ['MOBYLEHOME']
if not MOBYLEHOME:
    sys.exit('MOBYLEHOME must be defined in your environment')

if ( os.path.join( MOBYLEHOME , 'Src' ) ) not in sys.path:
    sys.path.append(  os.path.join( MOBYLEHOME , 'Src' )  )



import urllib, urllib2, cookielib #@UnresolvedImport

from Mobyle.ConfigManager  import Config
from Workflow import Parser

if __name__ == "__main__":
    cfg = Config()
    url = cfg.cgi_url()+'/workflow.py'

        
    # the cookie jar keeps the Mobyle session cookie in a warm place, so that 
    # all the HTTP requests connect to the same workspace 
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    mp = Parser()

    def get_str(params):
        data = urllib.urlencode(params)
        req = urllib2.Request(url, data)
        handle = opener.open(req)
        str = handle.read()
        return str.strip('\n')

    def get_xml(params):
        return mp.XML(get_str(params))
    
    # create a workflow and store its id
    params = {
              'object':'workflow',
              'action':'create'
              } 
    w = get_xml(params)
    print w
    
    # edit workflow properties
    params = {
              'object':'workflow',
              'action':'update',
              'workflow_id':w.id,
              'description':'test workflow description',
              'title':'test workflow title',
              }
    w = get_xml(params)
    print w
    
    # create the clustalw-multialign task
    params = {
              'object':'task',
              'action':'create',
              'workflow_id':w.id,
              'service_pid':'clustalw-multialign',
              }
    t = get_xml(params)
    print t

    # edit the clustalw-multialign task
    params = {
              'object':'task',
              'action':'update',
              'workflow_id':w.id,
              'task_id':t.id,
              'suspend':'false',
              'description':'Run a clustalw',
              }
    t = get_xml(params)
    print t
    
    # create the protdist task
    params = {
              'object':'task',
              'action':'create',
              'workflow_id':w.id,
              'service_pid':'protdist',
              }
    t = get_xml(params)
    print t

    # edit the protdist task
    params = {
              'object':'task',
              'action':'update',
              'workflow_id':w.id,
              'task_id':t.id,
              'suspend':'true',
              'description':'Run a protdist',
              }
    t = get_xml(params)
    print t

    # create the sequences input parameter
    params = {
              'object':'parameter',
              'action':'create',
              'workflow_id':w.id,
              'stream':'input',
              }
    p = get_xml(params)
    print p

    # edit the sequences parameter
    params = {
              'object':'parameter',
              'action':'update',
              'workflow_id':w.id,
              'parameter_id':p.id,
              'name': 'sequences',
              'prompt': 'Input sequences',
              'example': """>R
AAATA
>S
AAATT
              """,
              'datatype_class': 'Sequence',
              'biotype':'Protein'
              }
    p = get_xml(params)
    print p

    # create the format input parameter
    params = {
              'object':'parameter',
              'action':'create',
              'workflow_id':w.id,
              'stream':'input',
              }
    p = get_xml(params)
    print p

    # edit the sequences parameter
    params = {
              'object':'parameter',
              'action':'update',
              'workflow_id':w.id,
              'parameter_id':p.id,
              'name': 'alignment_format',
              'prompt': 'Alignment format',
              'datatype_class': 'String'
              }
    p = get_xml(params)
    print p

    # create the matrix output parameter
    params = {
              'object':'parameter',
              'action':'create',
              'workflow_id':w.id,
              'stream':'output',
              }
    p = get_xml(params)
    print p

    # edit the matrix output parameter
    params = {
              'object':'parameter',
              'action':'update',
              'workflow_id':w.id,
              'parameter_id':p.id,
              'name': 'matrix',
              'prompt': 'Distance matrix',
              'datatype_class': 'Matrix',
              'datatype_superclass': 'AbstractText',
              'biotype':'Protein'
              }
    p = get_xml(params)
    print p

    # create the sequences-to-clustalw link
    params = {
              'object':'link',
              'action':'create',
              'workflow_id':w.id,
              }
    l = get_xml(params)
    print l

    # edit the sequences-to-clustalw link
    params = {
              'object':'link',
              'action':'update',
              'workflow_id':w.id,
              'link_id':l.id,
              'from_parameter': '1',
              'to_task': '1',
              'to_parameter': 'infile'
              }
    p = get_xml(params)
    print p

    # create the alig_format-to-clustalw link
    params = {
              'object':'link',
              'action':'create',
              'workflow_id':w.id,
              }
    l = get_xml(params)
    print l

    # edit the alig_format-to-clustalw link
    params = {
              'object':'link',
              'action':'update',
              'workflow_id':w.id,
              'link_id':l.id,
              'from_parameter': '2',
              'to_task': '1',
              'to_parameter': 'outputformat'
              }
    p = get_xml(params)
    print p


    # create the clustalw-to-protdist link
    params = {
              'object':'link',
              'action':'create',
              'workflow_id':w.id,
              }
    l = get_xml(params)
    print l

    # edit the clustalw-to-protdist link
    params = {
              'object':'link',
              'action':'update',
              'workflow_id':w.id,
              'link_id':l.id,
              'from_task': '1',
              'from_parameter': 'aligfile',
              'to_task': '2',
              'to_parameter': 'infile'
              }
    p = get_xml(params)
    print p

    # create the protdist-to-output link
    params = {
              'object':'link',
              'action':'create',
              'workflow_id':w.id,
              }
    l = get_xml(params)
    print l

    # edit the protdist-to-output link
    params = {
              'object':'link',
              'action':'update',
              'workflow_id':w.id,
              'link_id':l.id,
              'from_task': '2',
              'from_parameter': 'outfile',
              'to_parameter': '3'
              }
    p = get_xml(params)
    print p
        
    # get the workflow
    params = {
              'object':'workflow',
              'action':'get',
              'workflow_id':w.id
              } 
    w = get_xml(params)
    print w

    # get the workflow
    params = {
              'object':'workflow',
              'action':'get_url',
              'workflow_id':w.id
              } 
    w = get_str(params)
    print "created workflow definition: %s" % w

    # list the session workflow IDs...
    params = {
              'object':'workflow',
              'action':'list'
              } 
    l = get_str(params)
    print "list of workflow definitions for current session: %s" % l
    
    url = cfg.cgi_url()+'/session_job_submit.py'
    params = {'workflowUrl': w,
    'sequences': """>A
TTTT

>B
TATA""",
    'alignment_format': 'PHYLIP',
    'email': 'hmenager@pasteur.fr'}
    resp = get_str(params)
    print resp
