import unittest2 as unittest
import os
import sys
import shutil

MOBYLEHOME = os.path.abspath( os.path.join( os.path.dirname( __file__ ) , "../../../" ) )
os.environ['MOBYLEHOME'] = MOBYLEHOME

if ( MOBYLEHOME ) not in sys.path:
    sys.path.append( MOBYLEHOME )
if ( os.path.join( MOBYLEHOME , 'Src' ) ) not in sys.path:    
    sys.path.append( os.path.join( MOBYLEHOME , 'Src' ) )

import Mobyle.Test.MobyleTest

tools_path = os.path.join( MOBYLEHOME , 'Tools' )
sys.path.append( tools_path )
mobdeploy_path = os.path.join( tools_path , 'mobdeploy' )
if not os.path.exists( mobdeploy_path + '.py' ):
    os.symlink( mobdeploy_path , mobdeploy_path + '.py' )
try:
    from Tools import mobdeploy
finally:
    os.unlink( mobdeploy_path + ".py" )


fake_mobyle_path = '/tmp/test_Mobyle'
DATADIR = os.path.dirname( __file__ )

class ServicesDeployerTest( unittest.TestCase ):
    
    def setUp(self):
        """ 
        setting up the configuration for the test, including:
        - test configuration that does not check dns or try to send confirmation emails
        - test session email
        """
        pass
    
    def tearDown(self):
        shutil.rmtree( fake_mobyle_path , ignore_errors= True )
        
        
    def testMakeTmp(self):
        pass
    def testSwitchDeployement(self):
        pass
    def testDoCommand(self):
        pass
    def testGet_registry_from_args(self):
        pass
    def testGet_registry_from_config(self):
        pass
    def testRecoverFromExisting(self):
        pass
    def testDo_cmd(self):
        pass
    def is_exported(self):
        pass
    def testGetOldXmlAsIs(self):
        pass
    def testGetXml(self):
        pass
    def testLoad_xsl_pipe(self):
        pass
    def testTemplate(self):
        pass
    def process_service(self):
        pass
    def testValidateOrDie(self):
        pass
    def tesMakeIndexes(self):
        pass
    
    
    