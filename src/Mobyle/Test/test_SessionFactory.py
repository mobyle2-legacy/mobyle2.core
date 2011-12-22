########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

import unittest2 as unittest
import os
import sys
import shutil

MOBYLEHOME = os.path.abspath( os.path.join( os.path.dirname( __file__ ) , "../../../" ) )
os.environ[ 'MOBYLEHOME' ] = MOBYLEHOME
if ( MOBYLEHOME ) not in sys.path:
    sys.path.append( MOBYLEHOME )
if ( os.path.join( MOBYLEHOME , 'Src' ) ) not in sys.path:    
    sys.path.append( os.path.join( MOBYLEHOME , 'Src' ) )
    
import Mobyle.Test.MobyleTest 
from Mobyle.SessionFactory import SessionFactory
from Mobyle.MobyleError import SessionError , AuthenticationError
from Mobyle.Net import Email , EmailAddress
Email.send = lambda templateName , subject , msg : None

class SessionFactoryTest(unittest.TestCase):
    
    
    def setUp(self):
        """ 
        setting up the configuration for the test, including:
          - test configuration that does not check dns or try to send confirmation emails
        """
        self.cfg = Mobyle.ConfigManager.Config()
        self.cfg._authenticated_session = 'yes'

        shutil.rmtree( self.cfg.test_dir , ignore_errors=True )
        os.makedirs( self.cfg.test_dir )

        self.sessionFactory = SessionFactory(self.cfg)
        self.sessionFactory._SessionFactory__sessions = {}
        
    def tearDown( self ):
        self.sessionFactory._SessionFactory__sessions = {}
        shutil.rmtree( self.cfg.test_dir , ignore_errors=True )
        
    def testAnonymousSessionNormalLifeCycle(self):
        ## Creation should fail if disabled
        self.cfg._anonymous_session = 'no'
        self.assertRaises( SessionError , self.sessionFactory.getAnonymousSession )
        ## Creation should succeed if enabled
        self.cfg._anonymous_session = 'yes'
        s1 = self.sessionFactory.getAnonymousSession()
        ## Fetch an existing session
        sessionID = s1.getKey()
        s2 = self.sessionFactory.getAnonymousSession( key = sessionID ) 
        self.assertEqual( s1 , s2 )
        ## Access should fail if missing
        self.sessionFactory.removeSession( sessionID )
        self.assertRaises( SessionError , self.sessionFactory.getAnonymousSession , key = sessionID )

    def testGetInvalidAnonymousSession(self):
        self.assertRaises( SessionError, self.sessionFactory.getAnonymousSession, "__invalid_key__")
    
    def testAuthenticatedSessionNormalLifeCycle(self):
        email = Mobyle.Net.EmailAddress( 'toto@123.com' )
        password = 'tutu'
        #test 
        self.assertRaises( SessionError, self.sessionFactory.getAuthenticatedSession, email , password )
        
        #create 
        s1 = self.sessionFactory.createAuthenticatedSession( email , password )
        sessionID = s1.getKey()
        
        #creation with same email , passwd
        self.assertRaises( AuthenticationError , self.sessionFactory.createAuthenticatedSession , email , password )
    
        s2 = self.sessionFactory.getAuthenticatedSession( email , password)
        self.assertEqual( s1 , s2 )
        self.sessionFactory.removeSession( sessionID )
        self.assertRaises( AuthenticationError , self.sessionFactory.getAuthenticatedSession, email , password )
        self.cfg._authenticated_session = 'no'
        self.assertRaises( SessionError , self.sessionFactory.createAuthenticatedSession , email , password )
        self.cfg._authenticated_session = 'yes'
        
    def testAuthenticatedSessionBadEmail(self):
        self.cfg._authenticated_session = 'email'
        To = 'toto@123.com'
        email1 = Mobyle.Net.EmailAddress( To )
        email2 = Mobyle.Net.EmailAddress( To + '.uk' )
        password = 'tutu'
        sess = self.sessionFactory.createAuthenticatedSession( email1 , password )
        self.assertRaises( AuthenticationError, self.sessionFactory.getAuthenticatedSession , email2 , password  )
        self.sessionFactory.removeSession( sess.getKey() )
        
    def testAuthenticatedSessionBadPasswd(self):
        email = Mobyle.Net.EmailAddress( 'toto@123.com' )
        password = 'tutu'
        sess = self.sessionFactory.createAuthenticatedSession( email , password )
        self.assertRaises( AuthenticationError , self.sessionFactory.getAuthenticatedSession , email , password + 'bad')
        self.sessionFactory.removeSession( sess.getKey() )        
 
    
    def testRemoveSession(self):
        email = Mobyle.Net.EmailAddress( 'toto@123.com' )
        password = 'tutu'
        sess = self.sessionFactory.createAuthenticatedSession( email , password )
        sessionDir = sess.getDir()
        sessKey = sess.getKey()
        self.sessionFactory.removeSession( sessKey )
        self.assertFalse( os.path.exists( sessionDir ) )
    
    def testOpenIdAuthenticatedSession(self):
        userEmailAddr = Mobyle.Net.EmailAddress( 'toto@123.com' )
        password = 'tutu'
        self.assertRaises( AuthenticationError, self.sessionFactory.getOpenIdAuthenticatedSession, userEmailAddr )
        self.cfg._authenticated_session = 'email'
        sess = self.sessionFactory.createAuthenticatedSession( userEmailAddr , password )
        ticket_id = sess.ticket_id
        session2 = self.sessionFactory.getOpenIdAuthenticatedSession( userEmailAddr , ticket_id=ticket_id )
        self.assertEqual( sess, session2 )
        
        #retirieve an existing session but not stored in factory
        del( self.sessionFactory._SessionFactory__sessions[ sess.getKey() ] )
        session3 = self.sessionFactory.getOpenIdAuthenticatedSession( userEmailAddr , ticket_id=ticket_id )
        self.assertEqual( sess.getDir() , session3.getDir() )
        
        
if __name__ == '__main__':
    unittest.main()
