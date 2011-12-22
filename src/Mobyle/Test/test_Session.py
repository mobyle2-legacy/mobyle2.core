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
from lxml import etree
from time import localtime, strftime

MOBYLEHOME = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
os.environ['MOBYLEHOME'] = MOBYLEHOME
if (MOBYLEHOME) not in sys.path:
    sys.path.append(MOBYLEHOME)
if (os.path.join(MOBYLEHOME, 'Src')) not in sys.path:    
    sys.path.append(os.path.join(MOBYLEHOME, 'Src'))

import Mobyle.Test.MobyleTest
import Mobyle.Session
from Mobyle.Classes.DataType import DataTypeFactory
from Mobyle.MobyleError import MobyleError, NoSpaceLeftError, SessionError, UserValueError
from Mobyle.Service import MobyleType
from Mobyle.Transaction import Transaction
from Mobyle.Utils import Admin

#tmpdir = '/tmp/mobyle'

class SessionTest(unittest.TestCase):

    def setUp(self):
        ## Config
        self.cfg = Mobyle.ConfigManager.Config()
        shutil.rmtree( self.cfg.test_dir , ignore_errors=True )
        ## Session
        self.session_key = 'fake_session'
        self.session = self._fakesession(self.session_key)
        ## Data
        self.data_name = 'datafile'
        self.data_text = 'A sample user data string'

    def tearDown(self):
        shutil.rmtree( self.cfg.test_dir , ignore_errors=True )

    ## Generic methods ...

    def testisLocal(self):
        self.assertTrue(self.session.isLocal())

    def testgetDir(self):
        xdir = os.path.join(self.cfg.user_sessions_path(), self.session_key)
        self.assertEqual(self.session.getDir(), xdir)

    def testgetKey(self):
        self.assertEqual(self.session.getKey(), self.session_key)

    def testgetBaseInfo(self):
        email = 'name@domain.ext'
        self.assertEqual(self.session.getBaseInfo(), (None, False, True))
        self.session.setEmail(email)
        self.assertEqual(self.session.getBaseInfo(), (email, False, True))

    def testisActivated(self):
        self.assertTrue(self.session.isActivated())

    def testgetEmail(self):
        email = 'name@domain.ext'
        self.assertEqual(self.session.getEmail(), None)
        self.session.setEmail(email)
        self.assertEqual(self.session.getEmail(), email)

    def testsetEmail(self):
        email = 'name@domain.ext'
        self.assertNotEqual(self.session.getEmail(), email)
        self.session.setEmail(email)
        self.assertEqual(self.session.getEmail(), email)
        ## Invalid email should be rejected
        self.assertRaises(UserValueError, self.session.setEmail, 'dummy')

    ## Data methods ...

    def testaddData(self):
        mtype = self._faketype('Text')
        ## Add data by content
        did = self.session.addData(self.data_name, mtype,
            content = self.data_text)
        self.assertTrue(self.session.hasData(did))
        session_data = os.path.join(self.session.getDir(), did)
        self.assertTrue(os.access(session_data, os.F_OK|os.R_OK))
        ## Add data from job
        url = self._fakejob('A00000000000000')
        job = Mobyle.MobyleJob.MobyleJob(ID = url)
        dat = os.path.join( job.getDir(), self.data_name )
        fh = open(dat, 'w')
        fh.write(self.data_text * 2)
        fh.close()
        did = self.session.addData(self.data_name, mtype,
            producer = job)
        self.assertTrue(self.session.hasData(did))
        session_data = os.path.join(self.session.getDir(), did)
        self.assertTrue(os.access(session_data, os.F_OK|os.R_OK))
        ## Add data from session
        session = self._fakesession('temp_session')
        did = session.addData(self.data_name, mtype,
            content = self.data_text)
        did = self.session.addData(did, mtype,
            producer = session)
        self.assertTrue(self.session.hasData(did))
        ## NEEDCARE: Data does not exists in source session or is private
        self.assertRaises(SessionError, self.session.addData, 'foobar', mtype,
            producer = session)
        ## Check that non file types are rejected
        mtype = self._faketype('String')
        self.assertRaises(MobyleError, self.session.addData, None, mtype,
            content = self.data_text)
        ## Check invalid combinations for content & producer
        mtype = self._faketype('Text')
        self.assertRaises(MobyleError, self.session.addData, None, mtype)
        self.assertRaises(MobyleError, self.session.addData, None, mtype,
            content = None, producer = None)
        self.assertRaises(MobyleError, self.session.addData, None, mtype,
            content = self.data_text, producer = job)
        ## Exceeding session size limit should fail
        self.session.sessionLimit = 0
        self.assertRaises(NoSpaceLeftError, self.session.addData, 'size', mtype,
            content = self.data_text * 10)

    def testremoveData(self):
        mtype = self._faketype('Text')
        did = self.session.addData(self.data_name, mtype,
            content = self.data_text)
        self.assertTrue(self.session.hasData(did))
        self.session.removeData(did)
        self.assertFalse(self.session.hasData(did))
        session_data = os.path.join(self.session.getDir(), did)
        self.assertFalse(os.access(session_data, os.F_OK))
        ## Cannot remove missing/private data
        self.assertRaises(SessionError, self.session.removeData, did)
        self.assertRaises(MobyleError, self.session.removeData,
            self.session.FILENAME)

    def testrenameData(self):
        user_name = 'userfile'
        mtype = self._faketype('Text')
        ## Add and rename data
        did = self.session.addData(self.data_name, mtype,
            content = self.data_text)
        self.assertNotEqual(self.data_name, user_name)
        self.session.renameData(did, user_name)
        ## Cannot rename a missing data
        self.assertRaises(SessionError, self.session.renameData, None,
            user_name)

    def testgetContentData(self):
        mtype = self._faketype('Text')
        lim = self.cfg.previewDataLimit()
        ## Add and get small data content
        did = self.session.addData(self.data_name, mtype,
            content = self.data_text)
        (flag, data) = self.session.getContentData(did)
        self.assertTrue(flag == 'FULL')
        self.assertTrue(data == self.data_text)
        ## Add/Get big data content
        did = self.session.addData(self.data_name, mtype,
            content = self.data_text * (lim / len(self.data_text) + 1))
        (flag, data) = self.session.getContentData(did)
        self.assertTrue(flag == 'HEAD')
        self.assertTrue(len(data) == self.cfg.previewDataLimit())
        (flag, data) = self.session.getContentData(did, False)
        self.assertTrue(flag == 'HEAD')
        self.assertTrue(len(data) == self.cfg.previewDataLimit())
        (flag, data) = self.session.getContentData(did, True)
        self.assertTrue(flag == 'FULL')
        self.assertTrue(len(data) > self.cfg.previewDataLimit())
        ## Cannot get content for missing/private data
        self.assertRaises(SessionError, self.session.getContentData, 'dummy')
        self.assertRaises(MobyleError, self.session.getContentData,
            self.session.FILENAME)

    def testgetDataSize(self):
        mtype = self._faketype('Text')
        ## Add data and get its size
        did = self.session.addData(self.data_name, mtype,
            content = self.data_text)
        size = self.session.getDataSize(did)
        self.assertEqual(size, len(self.data_text))
        ## Size from missing data should fail
        self.session.removeData(did)
        self.assertRaises(SessionError, self.session.getDataSize, did)

    def testhasData(self):
        mtype = self._faketype('Text')
        did = self.session.addData(self.data_name, mtype,
            content = self.data_text)
        self.assertTrue(self.session.hasData(did))
        self.session.removeData(did)
        self.assertFalse(self.session.hasData(did))

    def testgetAllData(self):
        mtype = self._faketype('Text')
        data = self.session.getAllData()
        self.assertTrue(len(data) == 0)
        self.session.addData(self.data_name, mtype,
            content = self.data_text)
        data = self.session.getAllData()
        self.assertTrue(len(data) == 1)
        self.session.addData(self.data_name, mtype,
            content = self.data_text * 2)
        data = self.session.getAllData()
        self.assertTrue(len(data) == 2)

    def testgetData(self):
        mtype = self._faketype('Text')
        ## Add and get data
        did = self.session.addData(self.data_name, mtype,
            content = self.data_text)
        data = self.session.getData(did)
        self.assertEqual(data['dataName'], did)
        ## Cannot get missing data
        self.session.removeData(did)
        self.assertRaises(SessionError, self.session.getData, did)

    ## Jobs methods ...

    def testhasJob(self):
        url = self._fakejob('A00000000000000')
        self.assertFalse(self.session.hasJob(url))
        self.session.addJob(url)
        self.assertTrue(self.session.hasJob(url))
        self.session.removeJob(url)
        self.assertFalse(self.session.hasJob(url))

    def testgetAllJobs(self):
        job_list = self.session.getAllJobs()
        self.assertTrue(len(job_list) == 0)
        url = self._fakejob('A00000000000000')
        self.session.addJob(url)
        job_list = self.session.getAllJobs()
        self.assertTrue(len(job_list) == 1)
        url = self._fakejob('A00000000000001')
        self.session.addJob(url)
        job_list = self.session.getAllJobs()
        self.assertTrue(len(job_list) == 2)
        ## Check cleaned job
        shutil.rmtree(Mobyle.JobState.url2path(url))
        job_list = self.session.getAllJobs()
        self.assertTrue(len(job_list) == 1)

    def testgetJob(self):
        url = self._fakejob('A00000000000000')
        ## Non existant job should fail
        self.assertRaises(SessionError, self.session.getJob, url)
        ## Add and get job
        self.session.addJob(url)
        job = self.session.getJob(url)
        self.assertTrue(job != None and job['jobID'] == url)
        ## Check cleaned (= directory removed) job
        shutil.rmtree(Mobyle.JobState.url2path(url))
        job = self.session.getJob(url)
        self.assertTrue(job == None)
        self.assertFalse(self.session.hasJob(url))

    def testrenameJob(self):
        url = self._fakejob('A00000000000000')
        name = 'new user job name'
        ## Non existant job should fail
        self.assertRaises(SessionError, self.session.renameJob, url, name)
        ## Add and rename job
        self.session.addJob(url)
        job = self.session.getJob(url)
        self.assertNotEqual(name, job['userName'])
        self.session.renameJob(url, name)
        job = self.session.getJob(url)
        self.assertEqual(name, job['userName'])

    def testaddJob(self):
        url = self._fakejob('A00000000000000')
        ## Add job
        self.assertFalse(self.session.hasJob(url))
        self.session.addJob(url)
        self.assertTrue(self.session.hasJob(url))
        ## Already added job should fail
        self.assertRaises(SessionError, self.session.addJob, url)

    def testremoveJob(self):
        url = self._fakejob('A00000000000000')
        ## Add and remove job
        self.assertFalse(self.session.hasJob(url))
        self.session.addJob(url)
        self.assertTrue(self.session.hasJob(url))
        self.session.removeJob(url)
        self.assertFalse(self.session.hasJob(url))
        ## Already removed job should fail
        self.assertRaises(SessionError, self.session.removeJob, url)

    def testjobExists(self):
        url = self._fakejob('A00000000000000')
        self.assertTrue(self.session.jobExists(url) == 1)
        shutil.rmtree(Mobyle.JobState.url2path(url))
        self.assertTrue(self.session.jobExists(url) == 0)


    def testSetAndGetJobLabel(self):
        #there is not labels yet in jobs
        url = self._fakejob('A00000000000000')
        self.session.addJob(url)
        label_recieved = self.session.getJobLabels(url)
        self.assertEqual( label_recieved , [] )
        #add one label
        label_send = ['label_1']
        self.session.setJobLabels( url , label_send )
        #get one label
        label_recieved = self.session.getJobLabels(url)
        self.assertEqual( label_recieved , label_send )
        #add 2 labels
        label_send = ['label_2', 'label_2_bis']
        self.session.setJobLabels( url , label_send )
        #get 2 labels
        label_recieved = self.session.getJobLabels(url)
        self.assertEqual( label_recieved , label_send )
        #add label in job which have already labels
        new_label = [ 'label_3', 'label_3_bis' ]
        self.session.setJobLabels( url , new_label )
        #get 2 new labels
        label_recieved = self.session.getJobLabels( url )
        label_recieved = self.session.getJobLabels( url )
        self.assertEqual( label_recieved , new_label )
        
        
    def testgetAllUniqueLabels(self):
        url = self._fakejob('A00000000000000')
        self.session.addJob(url)
        label_1= [ 'label_1', 'label_1_bis' ]
        label_2=  label_1 + [ 'label_2' ]
        self.session.setJobLabels( url , label_1 )
        self.session.setJobLabels( url , label_2 )
        label_recieved = self.session.getJobLabels( url )
        s = set( label_1 + label_2 )
        unique = list( s )
        unique.sort()
        label_recieved.sort()
        self.assertEqual( label_recieved , unique )
        
    def testSetAndGetJobDescription(self):
        url = self._fakejob('A00000000000000')
        self.session.addJob(url)
        job_description = "a new beautiful description for this job"
        self.session.setJobDescription( url , job_description)
        jobDescription_recieved = self.session.getJobDescription( url )
        self.assertEqual( jobDescription_recieved , job_description )
        url = self._fakejob('A00000000000001')
        self.session.addJob(url)
        jobDescription_recieved = self.session.getJobDescription( url )
        self.assertEqual( None , jobDescription_recieved )
        
    ## Workflow methods ...

    ## Utilities ...

    def _fakesession(self, key):
        session_key = key
        session_dir = os.path.join(self.cfg.user_sessions_path(), session_key)
        session = Mobyle.Session.Session(session_dir, session_key, self.cfg)
        os.makedirs(session_dir)
        session_xml = os.path.join(session_dir, session.FILENAME)
        Transaction.create(session_xml, False, True)
        return session

    def _faketype(self, mtype):
        dtf = DataTypeFactory()
        dtyp = dtf.newDataType(mtype)
        return MobyleType(dtyp, None)

    def _fakejob(self, key):
        job_name = 'fake_job'
        job_date = strftime("%x  %X", localtime())
        job_url = os.path.join(self.cfg.results_url(), job_name, key)
        job_dir = Mobyle.JobState.url2path(job_url)
        job_xml = os.path.join(job_dir, 'index.xml')
        os.makedirs(job_dir)
        ## index.xml
        root = etree.Element('jobState')
        node = etree.Element('date')
        node.text = job_date
        root.append(node)
        node = etree.Element('name')
        node.text = 'dummy.xml'
        root.append(node)
        node = etree.Element('id')
        node.text = job_url
        root.append(node)
        Mobyle.Utils.indent(root)
        fh = open(job_xml, 'w')
        fh.write(etree.tostring(root, xml_declaration=True, encoding='UTF-8'))
        fh.close()
        ## .admin
        #cwd = os.getcwd()
        #os.chdir(job_dir)
        Admin.create( job_dir, None, None, None)
        #os.chdir(cwd)
        return job_url

if __name__ == '__main__':
    unittest.main()

