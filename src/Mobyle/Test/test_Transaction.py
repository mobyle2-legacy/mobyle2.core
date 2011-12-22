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
os.environ['MOBYLEHOME'] = MOBYLEHOME

if ( MOBYLEHOME ) not in sys.path:
    sys.path.append( MOBYLEHOME )
if ( os.path.join( MOBYLEHOME , 'Src' ) ) not in sys.path:
    sys.path.append( os.path.join( MOBYLEHOME , 'Src' ) )

import Mobyle.Test.MobyleTest

from Mobyle.Transaction import Transaction
from Mobyle.MobyleError import MobyleError, SessionError
from Mobyle.Classes.DataType import DataTypeFactory
from Mobyle.Service import MobyleType
from Mobyle.Session import Session
#import Mobyle.Utils

DATADIR = os.path.dirname( __file__ )

class TransactionTest(unittest.TestCase):
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

        self.sessionKey = "Q12345678901234"
        self.sessionDir = os.path.join( self.cfg.test_dir , self.sessionKey )
        os.makedirs( self.sessionDir )

        self.email  = 'dummy@domain.fr'
        self.passwd = 'dummypass'
        self.actkey = 'dummykey'

        self.xmlSourcePath = os.path.join( DATADIR , 'session_test.xml')
        self.sessionPath = os.path.join( self.sessionDir , Session.FILENAME )
        self.dataID = [ "f835ddf28cb6aa776a41d7c71ec9cb5a.out" , "16bd6f89e732eb7cb0bbc13c65d202d3.aln" ]

        dtf = DataTypeFactory()
        dataType1   = dtf.newDataType( 'Sequence' )
        mobyleType1 = MobyleType( dataType1 , bioTypes = [ 'Protein' , 'Nucleic' ] , dataFormat =  'SWISSPROT' )
        dataType2   = dtf.newDataType( 'Alignment' )
        mobyleType2 = MobyleType( dataType2 , dataFormat = 'PHYLIPI' )
        self.datas  = [ {'dataName'   : 'f835ddf28cb6aa776a41d7c71ec9cb5a.out' ,
                        'userName'   : 'golden.out' ,
                        'size'       :   4410 ,
                        'Type'       :  mobyleType1 ,
                        'dataBegin'    :  'ID   104K_THEPA              Reviewed;         924' ,
                        'inputModes' : [ 'result' ] ,
                        'producedBy' : [ 'file://tmp/mobyle/results/dnadist/G25406684175968' ] ,
                        'usedBy'     : []
                        } ,
                        {'dataName'  : '16bd6f89e732eb7cb0bbc13c65d202d3.aln' ,
                         'userName'   : 'clustal.aln' ,
                         'size'       :    90044 ,
                         'Type'       :  mobyleType2 ,
                         'dataBegin'    :  '    47  1618\nF_75      ---------------------------' ,
                         'inputModes' : [ 'upload' , 'paste' ] ,
                         'producedBy' : [] ,
                         'usedBy'     : [ 'file://tmp/mobyle/results/dnadist/G25406684175968' ,
                                         'file://tmp/mobyle/results/dnadist/X25423048243999' ]
                         }
                        ]

        self.jobID = [ "file://tmp/mobyle/results/dnadist/X25423048243999" ,
                       "file://tmp/mobyle/results/dnadist/G25406684175968" ]
        self.jobs  = [ {'jobID'       : 'file://tmp/mobyle/results/dnadist/X25423048243999' ,
                      'userName'    : 'mon programme a moi' ,
                      'programName' : 'prog 1' ,
                      'status'      :  Mobyle.Status.Status( code = 6 ) , #killed
                      'date'        :  (2008, 11, 20, 12, 0, 0, 3, 325, -1) ,
                      'dataProduced': [] ,
                      'dataUsed'    : ['16bd6f89e732eb7cb0bbc13c65d202d3.aln'] ,
                      } ,
                      {'jobID'       : 'file://tmp/mobyle/results/dnadist/G25406684175968' ,
                       'userName'    : 'file://tmp/mobyle/results/dnadist/G25406684175968' ,
                       'programName' : 'dnadist' ,
                       'status'      :  Mobyle.Status.Status( code = 3 ) , #running
                       'date'        :  (2008, 11, 19, 10, 50, 33, 2, 324, -1) ,
                       'dataProduced': ['f835ddf28cb6aa776a41d7c71ec9cb5a.out'] ,
                       'dataUsed'    : ['16bd6f89e732eb7cb0bbc13c65d202d3.aln'] ,
                       }
                      ]

    def tearDown(self):
        shutil.rmtree( self.cfg.test_dir , ignore_errors= True )

    def testTransaction(self):
        Transaction.create( self.sessionPath , False , False )
        # Check locks types
        transaction = Transaction( self.sessionPath, Transaction.WRITE )
        transaction.rollback()
        transaction = Transaction( self.sessionPath, Transaction.READ )
        transaction.rollback()
        self.assertRaises(MobyleError, Transaction, self.sessionPath, None )
        # Invalid file
        self.assertRaises(SessionError, Transaction, str(None), Transaction.READ)

    def testCreation(self):
        #create( filename , authenticated , activated , activatingKey = None , email = None , passwd = None)

        #test anonymous session without email
        Transaction.create( self.sessionPath , False , False )
        os.unlink( self.sessionPath )

        #test anonymous session with passwd
        self.assertRaises( SessionError , Transaction.create , self.sessionPath , False , False , passwd = self.passwd )

        #test anonymous session with email
        Transaction.create( self.sessionPath , False , False , userEmail = self.email )
        os.unlink( self.sessionPath )

        #test authenticated session without passwd -> SessionError
        self.assertRaises( SessionError , Transaction.create , self.sessionPath , True , False , userEmail = self.email )

        #test authenticated session without email -> SessionError
        self.assertRaises( SessionError , Transaction.create , self.sessionPath , True , False , passwd = self.passwd )

        #test authenticated session with email and passwd
        Transaction.create( self.sessionPath , True , False , userEmail = self.email , passwd = self.passwd )
        os.unlink( self.sessionPath )

        #test authenticated session with activatingKey
        Transaction.create( self.sessionPath , True , False , activatingKey = self.actkey , userEmail = self.email , passwd = self.passwd )
        os.unlink( self.sessionPath )

        #test that session creation fails if already exists
        Transaction.create( self.sessionPath , False , False )
        self.assertRaises( SessionError , Transaction.create , self.sessionPath , False , False )
        os.unlink( self.sessionPath )

    def testCommit(self):
        Transaction.create( self.sessionPath , False , False )

        # Ensure that transaction with modification update the file
        bef = os.stat( self.sessionPath )
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        transaction._setModified( True )
        transaction.commit()
        aft = os.stat( self.sessionPath )
        self.assertFalse( bef.st_ino == aft.st_ino and bef.st_mtime == aft.st_mtime )

        # Ensure that transaction without modification does not update the file
        bef = os.stat( self.sessionPath )
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        transaction._setModified( False )
        transaction.commit()
        aft = os.stat( self.sessionPath )
        self.assertTrue( bef.st_ino == aft.st_ino and bef.st_mtime == aft.st_mtime )

        # By default, an empty transaction should have no effect on the file
        bef = os.stat( self.sessionPath )
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        transaction.commit()
        aft = os.stat( self.sessionPath )
        self.assertTrue( bef.st_ino == aft.st_ino and bef.st_mtime == aft.st_mtime )

    def testRollback(self):
        shutil.copy( self.xmlSourcePath , self.sessionPath )
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        transaction.removeData( self.dataID[0] )
        self. assertFalse( transaction.hasData(self.dataID[0] ) )
        transaction.rollback()
        transaction = Transaction( self.sessionPath , Transaction.READ )
        self.assertTrue( transaction.hasData( self.dataID[0] ) )
        transaction.commit()

    def testConcurency(self):
        Transaction.create( self.sessionPath , False , False )
        transaction = Transaction( self.sessionPath , Transaction.READ )
        ## sub-process start
        childPid = os.fork()
        if childPid: #father
            pid , status = os.wait()
            self.assertFalse( status )
        else: #child
            cmd = [ sys.executable, 'openTransaction.py' , self.sessionPath , str( Transaction.READ ) ]
            os.execv( cmd[0] , cmd )
        ## sub-process end
        transaction.commit()

        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        ## sub-process start
        childPid = os.fork()
        if childPid: #father
            pid , status = os.wait()
            self.assertTrue( status )
        else: #child
            cmd = [ sys.executable, 'openTransaction.py' , self.sessionPath , str( Transaction.READ ) ]
            os.execv( cmd[0] , cmd )
        ## sub-process end
        transaction.commit()

    def testgetID(self):
        Transaction.create( self.sessionPath , False , False )
        transaction = Transaction( self.sessionPath , Transaction.READ )
        receivedID = transaction.getID()
        transaction.commit()
        self.assertEqual( receivedID , self.sessionKey )

    def testEmail(self):
        Transaction.create( self.sessionPath , False , False )
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        transaction.setEmail( self.email )
        transaction.commit()
        transaction = Transaction( self.sessionPath , Transaction.READ )
        receivedEmail = transaction.getEmail()
        transaction.commit()
        self.assertTrue( receivedEmail == self.email )

    def testisActivated(self):
	# Test unactivated session
        Transaction.create( self.sessionPath , False , False )
        transaction = Transaction( self.sessionPath , Transaction.READ )
        active = transaction.isActivated()
        transaction.commit()
        self.assertFalse( active )
        os.unlink( self.sessionPath )

	# Test already activated session
        Transaction.create( self.sessionPath , False , True )
        transaction = Transaction( self.sessionPath , Transaction.READ )
        active = transaction.isActivated()
        transaction.commit()
        self.assertTrue( active )
        os.unlink( self.sessionPath )

	# Test session after activation
        Transaction.create( self.sessionPath , False , False )
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        transaction.activate()
        transaction.commit()
        transaction = Transaction( self.sessionPath , Transaction.READ )
        active = transaction.isActivated()
        transaction.commit()
        self.assertTrue( active )
        os.unlink( self.sessionPath )

     # Test session after inactivation
        Transaction.create( self.sessionPath , False , True )
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        active = transaction.isActivated()
        self.assertTrue( active )
        transaction.inactivate()
        transaction.commit()
        active = transaction.isActivated()
        self.assertFalse( active )
        os.unlink( self.sessionPath )


    def testActivatingKey(self):
        Transaction.create( self.sessionPath , False , True , activatingKey = self.actkey , userEmail = None)
        transaction = Transaction( self.sessionPath , Transaction.READ )
        actKey = transaction.getActivatingKey()
        transaction.commit()
        self.assertTrue( actKey == self.actkey )


    def testAuthenticated(self):
        Transaction.create( self.sessionPath , True , True , activatingKey = self.actkey , userEmail = self.email , passwd = self.passwd )
        transaction = Transaction( self.sessionPath , Transaction.READ )
        auth = transaction.isAuthenticated()
        transaction.commit()
        self.assertTrue( auth )


    def testPasswd(self):
        Transaction.create( self.sessionPath , False , False )
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        sendPasswd = "monBeauMotDePasse"
        transaction.setPasswd( sendPasswd )
        transaction.commit()
        transaction = Transaction( self.sessionPath , Transaction.READ )
        receivedPasswd =  transaction.getPasswd()
        transaction.commit()
        self.assertTrue( sendPasswd == receivedPasswd )


    def testCaptchaSolution( self ):
        sendSoluce = 'solution'
        Transaction.create( self.sessionPath , False , False )
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        transaction.setCaptchaSolution( sendSoluce )
        transaction.commit()
        transaction = Transaction( self.sessionPath , Transaction.READ )
        receivedSoluce = transaction.getCaptchaSolution()
        transaction.commit()
        self.assertTrue( sendSoluce == receivedSoluce )
        transaction2 = Transaction( self.sessionPath , Transaction.READ )
        receivedSoluce = transaction2.getCaptchaSolution()
        self.assertTrue( sendSoluce == receivedSoluce )
        transaction2.commit()

    ################################
    #
    #  operations on Data
    #
    #################################

    def testHasData(self):
        shutil.copy( self.xmlSourcePath , self.sessionPath)
        transaction = Transaction( self.sessionPath , Transaction.READ )
        self.assertTrue( transaction.hasData( self.dataID[1] ) )
        transaction.commit()

    def testRenameData( self ):
        shutil.copy( self.xmlSourcePath , self.sessionPath)
        newUserName = '__new_user_name_for_the_data__'
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        transaction.renameData( self.dataID[0] , newUserName )
        transaction.commit()
        transaction = Transaction( self.sessionPath , Transaction.READ )
        data = transaction.getData( self.dataID[0] )
        transaction.commit()
        self.assertTrue( newUserName == data[ 'userName' ] )

    def testGetAllData(self):
        shutil.copy( self.xmlSourcePath , self.sessionPath)
        transaction = Transaction( self.sessionPath , Transaction.READ )
        receivedData = transaction.getAllData()
        transaction.commit()
        self.assertTrue( len( receivedData ) == 2 )
        for data in receivedData:
            self.assertTrue( data in self.datas )

    def testRemoveData( self ):
        shutil.copy( self.xmlSourcePath , self.sessionPath )
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        transaction.removeData( self.dataID[0] )
        transaction.commit()
        transaction = Transaction( self.sessionPath , Transaction.READ )
        self.assertFalse( transaction.hasData( self.dataID[0] ) )
        transaction.commit()

    def testLinkJobInput2Data( self ):
        Transaction.create( self.sessionPath , False , True )
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        sendData = self.datas[0]
        transaction.createData( sendData[ 'dataName' ] ,
                                sendData[ 'userName' ] ,
                                sendData[ 'size' ] ,
                                sendData[ 'Type' ] ,
                                sendData[ 'dataBegin' ] ,
                                sendData[ 'inputModes' ] ,
                                producedBy = [] ,
                                usedBy = []
                                )
        sendJob = self.jobs[ 0 ]
        transaction.createJob( sendJob['jobID'] ,
                                sendJob['userName'] ,
                                sendJob['programName'] ,
                                sendJob['status'] ,
                                sendJob['date'] ,
                                [] ,
                                []
                                )
        transaction.commit()
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        transaction.linkJobInput2Data( [ sendData[ 'dataName' ] ] , [ sendJob['jobID'] ])
        transaction.commit()
        transaction = Transaction( self.sessionPath , Transaction.READ )
        data = transaction.getData( sendData[ 'dataName' ] )
        job = transaction.getJob( sendJob['jobID'])
        transaction.commit()
        self.assertEqual( data[ 'usedBy' ][0] , sendJob[ 'jobID' ] )
        self.assertEqual( job[ 'dataUsed' ][0] , sendData[ 'dataName' ] )

    def testLinkJobOutput2Data( self ):
        Transaction.create( self.sessionPath , False , True )
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        sendData = self.datas[0]
        transaction.createData( sendData[ 'dataName' ] ,
                                sendData[ 'userName' ] ,
                                sendData[ 'size' ] ,
                                sendData[ 'Type' ] ,
                                sendData[ 'dataBegin' ] ,
                                sendData[ 'inputModes' ] ,
                                producedBy = [] ,
                                usedBy = []
                                )
        sendJob = self.jobs[ 0 ]
        transaction.createJob( sendJob['jobID'] ,
                                sendJob['userName'] ,
                                sendJob['programName'] ,
                                sendJob['status'] ,
                                sendJob['date'] ,
                                [] ,
                                []
                                )
        transaction.commit()
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        transaction.linkJobOutput2Data( [ sendData[ 'dataName' ] ] , [ sendJob['jobID'] ])
        transaction.commit()
        transaction = Transaction( self.sessionPath , Transaction.READ )
        data = transaction.getData( sendData[ 'dataName' ] )
        job = transaction.getJob( sendJob['jobID'])
        transaction.commit()
        self.assertEqual( data[ 'producedBy' ][0] , sendJob[ 'jobID' ] )
        self.assertEqual( job[ 'dataProduced' ][0] , sendData[ 'dataName' ] )


    def testAddInputModes(self ):
        shutil.copy( self.xmlSourcePath , self.sessionPath )
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        transaction.addInputModes( self.dataID[0] , [ 'paste' , 'db' ] )
        transaction.commit()
        transaction = Transaction( self.sessionPath , Transaction.READ )
        data = transaction.getData( self.dataID[0] )
        transaction.commit()
        result = ['paste' , 'db' , 'result']
        result.sort()
        data[ 'inputModes' ].sort()
        self.assertEqual( data[ 'inputModes' ] , result )
        #an inputMode must not be twice in the xml
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        transaction.addInputModes( self.dataID[0] , [ 'paste' ] )
        transaction.commit()
        transaction = Transaction( self.sessionPath , Transaction.READ )
        data = transaction.getData( self.dataID[0] )
        transaction.commit()
        data[ 'inputModes' ].sort()
        self.assertEqual( data[ 'inputModes' ] , result )

    def testCreateAndGetData( self ):
        Transaction.create( self.sessionPath , True , True , activatingKey = 'uneJolieCle' , userEmail = self.email , passwd = self.passwd )
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        sendData = self.datas[0]
        transaction.createData( sendData[ 'dataName' ] ,
                                sendData[ 'userName' ] ,
                                sendData[ 'size' ] ,
                                sendData[ 'Type' ] ,
                                sendData[ 'dataBegin' ] ,
                                sendData[ 'inputModes' ] ,
                                producedBy = sendData[ 'producedBy' ] ,
                                usedBy = sendData[ 'usedBy' ]
                                )
        transaction.commit()
        transaction = Transaction( self.sessionPath , Transaction.READ )
        receivedData = transaction.getData( sendData[ 'dataName' ] )
        transaction.commit()
        self.assertTrue( receivedData == sendData )

    ####################
    #
    #   jobs methods
    #
    ####################

    def testHasJob( self ):
        shutil.copy( self.xmlSourcePath , self.sessionPath )
        jobid = "file://tmp/mobyle/results/dnadist/G25406684175968"
        transaction = Transaction( self.sessionPath , Transaction.READ )
        self.assertTrue( transaction.hasJob( jobid ) )
        self.assertFalse( transaction.hasJob( jobid.replace('G','Z') ) )
        transaction.commit()

    def testGetAllJobs( self ):
        shutil.copy( self.xmlSourcePath , self.sessionPath)
        transaction = Transaction( self.sessionPath , Transaction.READ )
        receivedJobs = transaction.getAllJobs()
        transaction.commit()
        self.assertTrue( len( receivedJobs ) == 2 )

        for job in receivedJobs:
            self.assertTrue( job in self.jobs )

    def testCreateAndGetJob( self ):
        Transaction.create( self.sessionPath , False , True )
        sendJob = self.jobs[ 1 ]
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        transaction.createJob( sendJob['jobID'] ,
                                sendJob['userName'] ,
                                sendJob['programName'] ,
                                sendJob['status'] ,
                                sendJob['date'] ,
                                sendJob['dataUsed'] ,
                                sendJob['dataProduced']
                                )
        transaction.commit()
        transaction = Transaction( self.sessionPath , Transaction.READ )
        receivedJob = transaction.getJob( sendJob[ 'jobID' ] )
        transaction.commit()
        self.assertEqual( sendJob , receivedJob )


    def testRemoveJob( self ):
        shutil.copy( self.xmlSourcePath , self.sessionPath )
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        transaction.removeJob( self.jobID[1] )
        transaction.commit()
        transaction = Transaction( self.sessionPath , Transaction.READ )
        self.assertFalse( transaction.hasJob( self.jobID[1] ) )
        transaction.commit()

    def testRenameJob( self ):
        shutil.copy( self.xmlSourcePath , self.sessionPath )
        newUserName = "mon beau job"
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        transaction.renameJob( self.jobID[1] , newUserName )
        transaction.commit()
        transaction = Transaction( self.sessionPath , Transaction.READ )
        job = transaction.getJob( self.jobID[1] )
        transaction.commit()
        self.assertEqual( newUserName , job[ 'userName' ] )

    def testUpdateJobStatus( self ):
        shutil.copy( self.xmlSourcePath , self.sessionPath )
        sendStatus = Mobyle.Status.Status( code = 7 ) #hold
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        transaction.updateJobStatus( self.jobID[0] , sendStatus )
        transaction.commit()
        transaction = Transaction( self.sessionPath , Transaction.READ )
        job = transaction.getJob( self.jobID[0] )
        transaction.commit()
        self.assertEqual( sendStatus , job[ 'status' ] )
        
    def testSetAndGetJobLabel(self):
        shutil.copy( self.xmlSourcePath , self.sessionPath )
        #there is not labels yet in jobs
        transaction = Transaction( self.sessionPath , Transaction.READ )
        label_recieved = transaction.getJobLabels(self.jobID[0])
        transaction.commit()
        self.assertEqual( label_recieved , [] )
        #add one label
        label_send = ['label_1']
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        transaction.setJobLabels( self.jobID[0] , label_send )
        transaction.commit()
        #get one label
        transaction = Transaction( self.sessionPath , Transaction.READ )
        label_recieved = transaction.getJobLabels(self.jobID[0])
        transaction.commit()
        self.assertEqual( label_recieved , label_send )
        #add 2 labels
        label_send = ['label_2', 'label_2_bis']
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        transaction.setJobLabels( self.jobID[1] , label_send )
        transaction.commit()
        #get 2 labels
        transaction = Transaction( self.sessionPath , Transaction.READ )
        label_recieved = transaction.getJobLabels(self.jobID[1])
        transaction.commit()
        self.assertEqual( label_recieved , label_send )
        #add label in job which have already labels
        new_label = [ 'label_3', 'label_3_bis' ]
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        transaction.setJobLabels( self.jobID[1] , new_label )
        transaction.commit()
        #get 2 new labels
        transaction = Transaction( self.sessionPath , Transaction.READ )
        label_recieved = transaction.getJobLabels( self.jobID[1] )
        label_recieved = transaction.getJobLabels( self.jobID[1] )
        transaction.commit()
        self.assertEqual( label_recieved , new_label )
        
        
    def testgetAllUniqueLabels(self):
        shutil.copy( self.xmlSourcePath , self.sessionPath )
        label_1= [ 'label_1', 'label_1_bis' ]
        label_2=  label_1 + [ 'label_2' ]
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        transaction.setJobLabels( self.jobID[0] , label_1 )
        transaction.setJobLabels( self.jobID[1] , label_2 )
        transaction.commit()
        transaction = Transaction( self.sessionPath , Transaction.READ )
        label_recieved = transaction.getJobLabels( self.jobID[1] )
        transaction.commit()
        s = set( label_1 + label_2 )
        unique = list( s )
        unique.sort()
        label_recieved.sort()
        self.assertEqual( label_recieved , unique )
        
    def testSetAndGetJobDescription(self):
        shutil.copy( self.xmlSourcePath , self.sessionPath )
        job_description = "a new beautiful description for this job"
        transaction = Transaction( self.sessionPath , Transaction.WRITE )
        transaction.setJobDescription( self.jobID[0] , job_description)
        transaction.commit()
        transaction = Transaction( self.sessionPath , Transaction.READ )
        jobDescription_recieved = transaction.getJobDescription( self.jobID[0] )
        transaction.commit()
        self.assertEqual( jobDescription_recieved , job_description )
        transaction = Transaction( self.sessionPath , Transaction.READ )
        jobDescription_recieved = transaction.getJobDescription( self.jobID[1] )
        transaction.commit()
        self.assertEqual( None , jobDescription_recieved )
        
        
if __name__ == '__main__':
    unittest.main()
