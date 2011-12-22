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
from Mobyle.ConfigManager import Config
from Workflow import Parser

if __name__ == "__main__":
    cfg = Config()
    url = cfg.cgi_url()+'/workflow.py'

        
    # the cookie jar keeps the Mobyle session cookie in a warm place, so that 
    # all the HTTP requests connect to the same workspace 
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPHandler(debuglevel=1),urllib2.HTTPCookieProcessor(cj))
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
              'suspend':'false',
              'description':'Run a clustalw',
              'parameter::infile':""">A
TTTT

>B
TATA""",
              'parameter::outputformat':'PHYLIP'
              }
    t = get_xml(params)
    print t
    
    # create the protdist task
    params = {
              'object':'task',
              'action':'create',
              'workflow_id':w.id,
              'service_pid':'protdist',
              'suspend':'true',
              'description':'Run a protdist',
              'from_task': '1',
              'from_parameter': 'aligfile',
              'to_task': 'self',
              'to_parameter': 'infile'
              }
    t = get_xml(params)
    print t
        
    # get the workflow
    params = {
              'object':'workflow',
              'action':'get',
              'workflow_id':w.id
              } 
    w = get_xml(params)
    print mp.tostring(w)

    # get the workflow
    params = {
              'object':'workflow',
              'action':'get_url',
              'workflow_id':w.id
              } 
    w = get_str(params)
    print "created workflow definition: %s" % w
#
    # list the session workflow IDs...
    params = {
              'object':'workflow',
              'action':'list'
              } 
    l = get_str(params)
    print "list of workflow definitions for current session: %s" % l
    
    url = cfg.cgi_url()+'/session_job_submit.py'
    params = {'workflowUrl': w}
    resp = get_str(params)
    print resp
