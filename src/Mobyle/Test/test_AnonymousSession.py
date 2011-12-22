########################################################################################
#                                                                                      #
#   Author: Bertrand Neron, Nicolas Joly                                               #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

import unittest2 as unittest
import os, sys
import shutil

MOBYLEHOME = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
os.environ['MOBYLEHOME'] = MOBYLEHOME
if (MOBYLEHOME) not in sys.path:
    sys.path.append(MOBYLEHOME)
if (os.path.join( MOBYLEHOME, 'Src')) not in sys.path:    
    sys.path.append(os.path.join(MOBYLEHOME, 'Src'))

import Mobyle.Test.MobyleTest
from Mobyle.AnonymousSession import AnonymousSession
from Mobyle.MobyleError import MobyleError, SessionError


class AnonymousSessionTest(unittest.TestCase):

    def setUp(self):
        self.cfg = Mobyle.ConfigManager.Config()
        shutil.rmtree( self.cfg.test_dir , ignore_errors=True )
        self.cfg._anonymous_session = 'yes'

    def tearDown(self):
        shutil.rmtree( self.cfg.test_dir , ignore_errors=True )

    def testAnonymousSession(self):
        ## Create a new session
        session = AnonymousSession(self.cfg)
        ## Fetch an existing session
        session_key = session.getKey()
        session = AnonymousSession(self.cfg, session_key)
        self.assertEqual(session.getKey(), session_key)
        ## Creation should fail if missing
        shutil.rmtree(session.getDir())
        self.assertRaises(MobyleError, AnonymousSession, self.cfg, session_key)
        ## Creation should fail if disabled
        self.cfg._anonymous_session = 'no'
        self.assertRaises(MobyleError, AnonymousSession, self.cfg)
        
    def testAlreadyExist(self):
        ## Creation should fail if no key is provided but the directory exist
        fake_key = 'A00000000000000'
        tmp_newSessionKey = AnonymousSession._AnonymousSession__newSessionKey
        AnonymousSession._AnonymousSession__newSessionKey = lambda x : fake_key
        dir = os.path.normpath( os.path.join( self.cfg.user_sessions_path() , AnonymousSession.DIRNAME , fake_key ) )
        os.makedirs( dir , 0755 )
        self.assertRaises(SessionError, AnonymousSession, self.cfg )
        AnonymousSession._AnonymousSession__newSessionKey = tmp_newSessionKey
    
    def testNoPermission(self):
        session_dir = os.path.normpath( os.path.join( self.cfg.user_sessions_path()  ) )
        os.makedirs( session_dir , 0755 )
        os.chmod( session_dir , 0000 )
        self.assertRaises(SessionError, AnonymousSession, self.cfg )
                                       
    def testisAuthenticated(self):
        session = AnonymousSession(self.cfg)
        self.assertFalse(session.isAuthenticated())

if __name__ == '__main__':
    unittest.main()
