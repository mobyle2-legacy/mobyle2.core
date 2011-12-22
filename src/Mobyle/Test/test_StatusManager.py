########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

import unittest2 as unittest
import os, sys, fcntl, signal
import shutil
from lxml import etree
from time import sleep

MOBYLEHOME = os.path.abspath( os.path.join( os.path.dirname( __file__ ) , "../../../" ) )
os.environ['MOBYLEHOME'] = MOBYLEHOME

if ( MOBYLEHOME ) not in sys.path:
    sys.path.append( MOBYLEHOME )
if ( os.path.join( MOBYLEHOME , 'Src' ) ) not in sys.path:
    sys.path.append( os.path.join( MOBYLEHOME , 'Src' ) )

import Mobyle.Test.MobyleTest
from Mobyle.StatusManager import StatusManager
from Mobyle.Status import Status

DATADIR = os.path.dirname( __file__ )

def handler(signum, frame):
    pass

class StatusManagerTest(unittest.TestCase):
    """Tests the functionalities of Transaction"""

    def setUp(self):
        """
        setting up the configuration for the test, including:
        - test configuration that does not check dns or try to send confirmation emails
        - test session email
        """
        self.cfg = Mobyle.ConfigManager.Config()
        shutil.rmtree(self.cfg.test_dir, ignore_errors=True)
        os.makedirs(self.cfg.test_dir)
        self.jobKey = "Q12345678901234"
        self.jobDir = os.path.join( self.cfg.test_dir , self.jobKey )
        os.makedirs( self.jobDir )
        self.filename = os.path.join( self.jobDir , StatusManager.file_name )

    def tearDown(self):
        shutil.rmtree( self.cfg.test_dir , ignore_errors= True )

    def testCreation(self):
        #create( filename , status )
        unknown = Status( code = -1 )
        StatusManager.create( self.jobDir , unknown )
        doc = etree.parse( self.filename )
        root = doc.getroot()
        self.assertEqual( root.tag , 'status' )
        children = list(root)
        self.assertEqual( len( children ) , 2 )
        self.assertEqual( children[0].tag , 'value')
        self.assertEqual( children[0].text , 'unknown' )
        self.assertEqual( children[1].tag , 'message')
        self.assertEqual( children[1].text , None )
        os.unlink( self.filename )

        building = Status( code = 0 )
        StatusManager.create( self.jobDir, building )
        doc = etree.parse( self.filename )
        root = doc.getroot()
        self.assertEqual( root.tag , 'status' )
        children = list(root)
        self.assertEqual( len( children ) , 2 )
        self.assertEqual( children[0].tag , 'value')
        self.assertEqual( children[0].text , 'building' )
        self.assertEqual( children[1].tag , 'message')
        self.assertEqual( children[1].text , None )
        os.unlink( self.filename )

        submitted = Status( code = 1, message= 'test message' )
        StatusManager.create( self.jobDir, submitted )
        doc = etree.parse( self.filename )
        root = doc.getroot()
        self.assertEqual( root.tag , 'status' )
        children = list(root)
        self.assertEqual( len( children ) , 2 )
        self.assertEqual( children[0].tag , 'value')
        self.assertEqual( children[0].text , 'submitted' )
        self.assertEqual( children[1].tag , 'message')
        self.assertEqual( children[1].text , 'test message' )
        os.unlink( self.filename )

        running = Status( string='running' )
        StatusManager.create( self.jobDir, running )
        doc = etree.parse( self.filename )
        root = doc.getroot()
        self.assertEqual( root.tag , 'status' )
        children = list(root)
        self.assertEqual( len( children ) , 2 )
        self.assertEqual( children[0].tag , 'value')
        self.assertEqual( children[0].text , 'running' )
        self.assertEqual( children[1].tag , 'message')
        self.assertEqual( children[1].text , None )
        os.unlink( self.filename )


    def testGetStatus( self ):
        running = Status( string='running' )
        StatusManager.create( self.jobDir, running )
        sm = StatusManager()
        recieved_status = sm.getStatus( self.jobDir )
        self.assertEqual( recieved_status , running )
        os.unlink( self.filename )

        killed = Status( string='killed' , message= "your job has been canceled" )
        StatusManager.create( self.jobDir, killed )
        sm = StatusManager()
        recieved_status = sm.getStatus( self.jobDir )
        self.assertEqual( recieved_status , killed )
        os.unlink( self.filename )


    def testSetstatus( self):
        StatusManager.create( self.jobDir, Status( string='submitted' ) )

        pending = Status( string= 'pending' )
        sm = StatusManager()
        sm.setStatus( self.jobDir , pending )
        recieved_status = sm.getStatus( self.jobDir )
        self.assertEqual( recieved_status , pending )

        finished = Status( string='finished' , message = 'your job finnished with an unusual status code, check youre results carefully')
        sm.setStatus( self.jobDir , finished )
        recieved_status = sm.getStatus( self.jobDir )
        self.assertEqual( recieved_status , finished )

        #an ended status cannot be changed anymore
        running = Status( string= 'running')
        sm.setStatus( self.jobDir , running )
        recieved_status = sm.getStatus( self.jobDir )
        self.assertNotEqual( recieved_status , running )
        self.assertEqual( recieved_status , finished )
        os.unlink( self.filename )

    def testConcurency(self):
        status = Status( string='submitted' )
        StatusManager.create( self.jobDir, status )

        ## sub-process start
        childPid = os.fork()
        if childPid: #father
            sleep(1)
            sm = StatusManager()
            self.assertEqual( status , sm.getStatus( self.jobDir ) )
            self.assertRaises( IOError , sm.setStatus , self.jobDir, status )
            os.kill( childPid , signal.SIGALRM )
            os.wait()

        else: #child
            signal.signal(signal.SIGALRM, handler)
            File = open( self.filename , 'r' )
            fcntl.lockf( File , fcntl.LOCK_SH | fcntl.LOCK_NB )
            signal.pause()
            fcntl.lockf( File , fcntl.LOCK_UN  )
            File.close()
            os._exit(0)
        ## sub-process end

        ## sub-process start
        childPid = os.fork()
        if childPid: #father
            sleep(1)
            sm = StatusManager()
            recieved_status = sm.getStatus( self.jobDir )
            self.assertEqual( recieved_status , Status( string= "unknown" )  )
            self.assertRaises( IOError , sm.setStatus , self.jobDir, status )
            os.kill( childPid , signal.SIGALRM )
            os.wait()

        else: #child
            signal.signal(signal.SIGALRM, handler)
            File = open( self.filename , 'r+' )
            fcntl.lockf( File , fcntl.LOCK_EX | fcntl.LOCK_NB )
            signal.pause()
            fcntl.lockf( File , fcntl.LOCK_UN  )
            File.close()
            os._exit(0)
        ## sub-process end


if __name__ == '__main__':
    unittest.main()
