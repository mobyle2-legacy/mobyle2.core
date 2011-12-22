#############################################################
#                                                           #
#   Author: Herve Menager                                   #
#   Organization:'Biological Software and Databases' Group, #
#                Institut Pasteur, Paris.                   #
#   Distributed under GPLv2 Licence. Please refer to the    #
#   COPYING.LIB document.                                   #
#                                                           #
#############################################################
"""
Validator.py

This module is used to validate a Mobyle XML file (program or else?)
against the Relax NG schema and the schematron rules
- The Validator class
"""
from lxml import etree
import os
from subprocess import Popen, PIPE
from Mobyle.ConfigManager import Config
_cfg = Config()

from logging import getLogger
v_log = getLogger(__name__)

# defining paths for validation external stuff
mobschPath = os.path.join(_cfg.mobylehome(),'Schema','mobyle.sch')
schprocPath = os.path.join(_cfg.mobylehome(),'Tools','validation','iso_svrl.xsl')
rbPath = os.path.join(_cfg.mobylehome(),'Tools','validation','remove_base.xsl')
jingPath = os.path.join(_cfg.mobylehome(),'Tools','validation','jing','jing.jar')

SVRL_NS = "http://purl.oclc.org/dsdl/svrl"
svrl_validation_errors = etree.XPath(
    '//svrl:failed-assert/svrl:text/text()', namespaces={'svrl': SVRL_NS})

# generating schematron validation xsl from its xsl generator
schVal_transform = etree.XSLT(etree.parse(schprocPath))
mobVal_transform = etree.XSLT(schVal_transform(etree.parse(mobschPath)))


rb_transform = etree.XSLT(etree.parse(rbPath))

net_enabled_parser = etree.XMLParser(no_network=False)

class Validator(object):
    
    def __init__(self, type, docPath=None, docString=None, publicURI=None,runRNG=True, runSCH=True, runRNG_Jing=False):
        assert (docPath is not None and docString is None) or (docPath is None and docString is not None), "Please specify either a path or a string. Your parameters:\n-path=%s\n-string=%s" %(docPath, docString)
        types = ["program", "viewer", "workflow", "program_or_workflow"]
        assert type in types, "Supported validator types are: %s - not %s" % (', '.join(types), type)

        self.publicURI = publicURI
        self.mobrngPath = os.path.join(_cfg.mobylehome(),'Schema','%s.rng' % type)
        rng_doc = etree.parse(self.mobrngPath)
        self.mobrngVal = etree.RelaxNG(rng_doc)
        
        self.runRNG = runRNG
        self.runRNG_Jing = runRNG_Jing
        self.runSCH = runSCH
        
        self.docPath = docPath
                    
        if docPath:        
            self.doc = etree.parse(docPath, parser=net_enabled_parser)
        else:
            self.doc = etree.fromstring(docString)
        self.doc.xinclude()
        self.doc = rb_transform(self.doc)

    def run(self):
        if self.runRNG:
            self.rngOk = self.mobrngVal.validate(self.doc)
            self.rngErrors = [self.mobrngVal.error_log.last_error]
        if self.runRNG_Jing:
            cp = '-cp %s' % jingPath
            val_cmd = ("java -Dorg.apache.xerces.xni.parser.XMLParserConfiguration=org.apache.xerces.parsers.XIncludeParserConfiguration %s com.thaiopensource.relaxng.util.Driver %s %s" % (cp, self.mobrngPath, self.docPath))
            val_cmd = val_cmd.split(' ')
            process = Popen(val_cmd , shell = False , stdout = PIPE, stderr = PIPE )
            messages = []
            for line in process.stdout:
                if line.find('found attribute "xml:base", but no attributes allowed here')==-1:
                    messages.append(line)
            for line in process.stderr:
                if line.find('found attribute "xml:base", but no attributes allowed here')==-1:
                    messages.append(line)
            process.wait()
            #returnCode = process.poll()
            #self.rng_JingOk = not(returnCode)
            self.rng_JingOk = len(messages)==0
            self.rng_JingErrors = messages
        if self.runSCH:
            topLevelParams={}
            if self.publicURI:
                topLevelParams={'fileNameParameter':os.path.basename(self.publicURI)}
            self.eval_report = mobVal_transform(self.doc, **topLevelParams)
            self.schErrors = [s.strip() for s in svrl_validation_errors(self.eval_report)]
            self.schOk = len(self.schErrors)==0
            
        self.valNotOk = (self.runRNG and not(self.rngOk)) or (self.runSCH and not(self.schOk))
        self.valOk = not(self.valNotOk)
