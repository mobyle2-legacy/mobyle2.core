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
from lxml import etree

MOBYLEHOME = os.path.abspath( os.path.join( os.path.dirname( __file__ ) , "../../../" ) )
os.environ[ 'MOBYLEHOME' ] = MOBYLEHOME
if ( MOBYLEHOME ) not in sys.path:
    sys.path.append( MOBYLEHOME )
if ( os.path.join( MOBYLEHOME , 'Src' ) ) not in sys.path:
    sys.path.append( os.path.join( MOBYLEHOME , 'Src' ) )


import Mobyle.Test.MobyleTest
from Mobyle.AuthenticatedSession import AuthenticatedSession
from Mobyle.AnonymousSession import AnonymousSession
from Mobyle.Session import Session
from Mobyle.Transaction import Transaction
from Mobyle.MobyleError import SessionError , AuthenticationError
from Mobyle.Net import Email , EmailAddress
Email.send = lambda templateName , subject , msg : None
from Mobyle import JobState
from Mobyle.Registry import ProgramDef

DATADIR = os.path.dirname( __file__ )


class AuthenticatedSessionTest(unittest.TestCase):
    """Tests the functionalities of Transaction"""

    def setUp( self ):
        self.cfg = Mobyle.ConfigManager.Config()
        self.cfg._authenticated_session = 'yes'

        shutil.rmtree( self.cfg.test_dir , ignore_errors= True )
        os.makedirs( self.cfg.test_dir )
        os.makedirs( self.cfg.user_sessions_path() )

        self.registry = Mobyle.Session.registry

        self.fake_prg = ProgramDef( self.registry.getProgramUrl( name = 'fake' ),
                                    name = 'fake',
                                    path = self.registry._computeProgramPath( 'fake' ),
                                    server = self.registry.serversByName[ 'local' ]
                                   )
        self.registry.addProgram( self.fake_prg )
        self.passwd = "un_mot_de_pass"
        self.email = EmailAddress( "test@mondomain.fr" )

    def tearDown( self ):
        self.registry.pruneService(self.fake_prg )
        shutil.rmtree( self.cfg.user_sessions_path() , ignore_errors= True )
        shutil.rmtree( self.cfg.test_dir , ignore_errors= True )

    def testGetSessionWithPasswd(self):
        ## Create a new session
        session1 = AuthenticatedSession( self.cfg , self.email , passwd= self.passwd )
        ## Fetch an existing session
        session2 = AuthenticatedSession( self.cfg , self.email , passwd= self.passwd )
        self.assertEqual( session1.getDir() , session2.getDir() )
        self.assertRaises( AuthenticationError , AuthenticatedSession, self.cfg, self.email , passwd= 'bad_'+self.passwd )
        ## Creation should fail if disabled
        self.cfg._authenticated_session = 'no'
        self.assertRaises( SessionError , AuthenticatedSession, self.cfg, self.email , passwd= self.passwd )
        self.cfg._authenticated_session = 'yes'
        ##try to authenticated with an invalid email
        session1._AuthenticatedSession__userEmail.check = lambda x: False
        session2 = AuthenticatedSession( self.cfg , self.email , passwd= self.passwd )

    def testGetSessionWithTicket(self):
        ## Create a new session
        self.cfg._authenticated_session = 'email'
        # BUG?
        #pourquoi un ticket n'est cree que dans le cas self.cfg._authenticated_session = 'email'
        #et pas quand self.cfg._authenticated_session = 'yes' ????
        session1 = AuthenticatedSession( self.cfg , self.email , passwd= self.passwd )
        ## Fetch an existing session
        session2 = AuthenticatedSession( self.cfg , self.email , ticket_id= session1.ticket_id )
        self.assertEqual( session1.getDir() , session2.getDir() )
        self.assertRaises( SessionError, AuthenticatedSession, self.cfg , self.email , ticket_id= session1.ticket_id+"1" )


    def testCheckPasswd( self ):
        session = AuthenticatedSession( self.cfg , self.email , passwd= self.passwd )
        self.assertFalse( session.checkPasswd( self.passwd + "false") )
        self.assertFalse( session.checkPasswd( "" ) )
        self.assertTrue( session.checkPasswd( self.passwd ) )
        newPasswd = "new_pass_word"
        session.setPasswd( newPasswd )
        self.assertFalse( session.checkPasswd( self.passwd ) )
        self.assertTrue( session.checkPasswd( newPasswd ) )
        #restore the passwd to test the other methods or further tests
        #self.session.changePasswd( newPasswd , self.passwd )

    def testChangePasswd( self ):
        session = AuthenticatedSession( self.cfg , self.email , passwd= self.passwd )
        newPasswd = "new_pass_word"
        self.assertRaises( AuthenticationError , session.changePasswd , self.passwd + "false" , newPasswd )
        session.changePasswd( self.passwd , newPasswd )
        self.assertTrue( session.checkPasswd( newPasswd ))
        #restore the passwd to test the other methods or further tests
        #session.changePasswd( newPasswd , self.passwd )


    def testConfirmEmail( self ):
        self.cfg._authenticated_session = 'email'
        session = AuthenticatedSession( self.cfg , self.email , passwd= self.passwd )
        transaction = session._getTransaction( Transaction.READ )
        actKey = transaction.getActivatingKey()
        transaction.commit()

        self.assertFalse( session.isActivated() )
        self.assertRaises( AuthenticationError , session.confirmEmail , actKey + "False")
        session.confirmEmail( actKey )
        self.assertTrue( session.isActivated() )

    def testMergeWith( self ):
        ## Create an authenticated session
        auth_session = AuthenticatedSession( self.cfg , self.email , passwd = self.passwd )
        ## Merging a session with itself should fail
        self.assertRaises( SessionError , auth_session.mergeWith , auth_session )
        ## Create an anonymous session
        self.cfg._anonymous_session = 'yes'
        key = 'anonymous_01'
        self._makeFakeSession( key )
        anno_session = AnonymousSession( self.cfg , key = key )
        jobs = anno_session.getAllJobs()
        datas = anno_session.getAllData()
        ## Merge sessions
        auth_session.mergeWith( anno_session )
        newJobs = auth_session.getAllJobs()
        newDatas = auth_session.getAllData()
        self.assertEqual( jobs , newJobs )
        self.assertEqual( datas , newDatas )

    def _makeFakeSession(self , key ):
        sessionPath  = os.path.join( self.cfg.user_sessions_path() , AnonymousSession.DIRNAME , key )
        if not os.path.exists( sessionPath ):
            os.makedirs( sessionPath , 0755)

        if os.path.exists( sessionPath ):
            shutil.rmtree( sessionPath )
        shutil.copytree( os.path.join( DATADIR , 'fake_session' ) , sessionPath )
        jobID = [ self.cfg.results_url() + "/fake_job/A00000000000000" ,
                  self.cfg.results_url() + "/fake_job/A00000000000001" ,
                  self.cfg.results_url() + "/fake_job/A00000000000002" ,
                ]
        xmlpath = os.path.join( sessionPath , Session.FILENAME )

        doc = etree.parse( "file://%s" % xmlpath )
        root = doc.getroot()

        jobNodes = root.xpath( 'jobList/job' )
        for jobNode in jobNodes:
            id = jobNode.get( 'id' )
            jobURL = jobID[ int(id) ]
            jobNode.set( 'id' , jobURL )

        producedByNodes = root.xpath( 'dataList/data/producedBy' )
        for producedByNode in producedByNodes:
            ref = producedByNode.get( 'ref' )
            jobURL = jobID[ int( ref ) ]
            producedByNode.set( 'ref' , jobURL )

        usedByNodes = root.xpath( 'dataList/data/usedBy' )
        for uesdByNode in usedByNodes:
            ref = uesdByNode.get( 'ref' )
            jobURL = jobID[ int( ref ) ]
            uesdByNode.set( 'ref' , jobURL )

        xmlfile = open( xmlpath , 'w' )
        xmlfile.write( etree.tostring( root , xml_declaration=True , encoding='UTF-8', pretty_print= True ) )
        xmlfile.close()

        for jobURL in  jobID:
            self._makeFakeJob( jobURL )

        return sessionPath


    def _makeFakeJob(self , jobID ):
        jobPath = JobState.url2path( jobID )
        jobdir = os.path.dirname( jobPath )
        if not os.path.exists( jobdir ):
            os.makedirs( jobdir , 0755)

        if os.path.exists( jobPath ):
            shutil.rmtree( jobPath )
        index = jobID[-1]

        shutil.copytree( os.path.join( DATADIR , 'fake_job'+ index ) , jobPath )

        doc = etree.parse( "file://%s/index.xml" % jobPath )
        root = doc.getroot()

        text_node = root.find( 'name' )
        text_node.text = Mobyle.Session.registry.serversByName[ 'local' ].jobsBase  + '/fake.xml'

        text_node = root.find( 'host' )
        text_node.text = self.cfg.root_url()

        text_node = root.find( 'id' )
        text_node.text = jobID

        xmlfile = open( os.path.join( jobPath , 'index.xml' ) , 'w' )
        xmlfile.write( etree.tostring( root , xml_declaration=True , encoding='UTF-8', pretty_print= True ) )
        xmlfile.close()

        return jobPath


if __name__ == '__main__':
    unittest.main()
