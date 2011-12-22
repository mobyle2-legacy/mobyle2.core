########################################################################################
#                                                                                      #
#   Author: Nicolas Joly                                                               #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

import unittest2 as unittest
import os, sys, stat
import shutil
from time import mktime

MOBYLEHOME = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
os.environ['MOBYLEHOME'] = MOBYLEHOME
if (MOBYLEHOME) not in sys.path:
    sys.path.append(MOBYLEHOME)
if (os.path.join(MOBYLEHOME, 'Src')) not in sys.path:
    sys.path.append(os.path.join(MOBYLEHOME, 'Src'))

import Mobyle.Test.MobyleTest
from Mobyle.MobyleError import MobyleError
from Mobyle.Admin import Admin


class AdminTest(unittest.TestCase):

    def setUp(self):
        ## Config
        self.cfg = Mobyle.ConfigManager.Config()
        ## Inits
        shutil.rmtree(self.cfg.test_dir, ignore_errors=True)
        os.makedirs(self.cfg.test_dir)
        self.cwd = os.getcwd()
        os.chdir(self.cfg.test_dir)
        ## Admin
        self.adm = self._fakeadmin()

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.cfg.test_dir)

    def testAdmin(self):
        ## Check valid paths
        Admin(".")
        Admin(Admin.FILENAME)
        ## Check invalid paths
        adm_dir = "dummy"
        self.assertRaises(MobyleError, Admin, adm_dir)
        os.makedirs(adm_dir)
        self.assertRaises(MobyleError, Admin, adm_dir)
        ## Empty file (fails silently)
        open(Admin.FILENAME, 'w').close()
        Admin(Admin.FILENAME)
        ## Missing read permissions
        os.chmod(Admin.FILENAME, 0222)
        self.assertRaises(MobyleError, Admin, ".")

    def testcreate(self):
        ## Create a minimal admin file
        os.unlink(Admin.FILENAME)
        Admin.create(self.cfg.test_dir, None, None, None)
        ## Should fail if already exists
        self.assertTrue(os.access(Admin.FILENAME, os.F_OK))
        self.assertRaises(MobyleError, Admin.create, self.cfg.test_dir, None, None, None)
        ## Check alternate path
        altdir = os.path.join(self.cfg.test_dir, "alternate")
        os.makedirs(altdir)
        Admin.create(altdir, None, None, None)

    def testrefresh(self):
        adm_queue = 'mobyle'
        self.assertEqual(self.adm.getQueue(), None)
        adm = Admin(Admin.FILENAME)
        adm.setQueue(adm_queue)
        adm.commit()
        self.assertEqual(self.adm.getQueue(), None)
        self.adm.refresh()
        self.assertEqual(self.adm.getQueue(), adm_queue)

    def testcommit(self):
        ## Commit should update file
        bef = os.stat(Admin.FILENAME)
        adm = Admin(Admin.FILENAME)
        adm.commit()
        aft = os.stat(Admin.FILENAME)
        self.assertTrue(bef.st_ino != aft.st_ino and bef.st_mtime <= aft.st_mtime)
        ## Cannot create/rename temporary file
        mod = os.stat(".").st_mode
        os.chmod(".", mod & ~stat.S_IWUSR)
        self.assertRaises(MobyleError, adm.commit)
        os.chmod(".", mod)
        ## Nothing to save (fails silently)
        adm.me.clear()
        adm.commit()

    def testDate(self):
        ## Ensure this is a valid date
        date = self.adm.getDate()
        mktime(date)
        ## Missing key
        self.adm.me.clear()
        self.assertEqual(self.adm.getDate(), None)

    def testEmail(self):
        adm_email = "user@domain.fr"
        ## Created without email info
        os.unlink(Admin.FILENAME)
        Admin.create(self.cfg.test_dir, None, None, None)
        adm = Admin(Admin.FILENAME)
        self.assertEqual(adm.getEmail(), None)
        ## Created with email info
        os.unlink(Admin.FILENAME)
        Admin.create(self.cfg.test_dir, None, None, None, userEmail=adm_email)
        adm = Admin(".")
        self.assertEqual(adm.getEmail(), adm_email)
        ## Missing key
        adm.me.clear()
        self.assertEqual(adm.getEmail(), None)

    def testRemote(self):
        adm_remote = "127.0.0.1/localhost"
        ## Created without remote info
        os.unlink(Admin.FILENAME)
        Admin.create(self.cfg.test_dir, None, None, None)
        adm = Admin(Admin.FILENAME)
        self.assertEqual(adm.getRemote(), str(None))
        ## Created with remote info
        os.unlink(Admin.FILENAME)
        Admin.create(self.cfg.test_dir, adm_remote, None, None)
        adm = Admin(Admin.FILENAME)
        self.assertEqual(adm.getRemote(), adm_remote)
        ## Missing key
        adm.me.clear()
        self.assertEqual(adm.getRemote(), None)

    def testWorkflow(self):
        workflowID = "adm_dummy"
        ## Created without session info
        os.unlink(Admin.FILENAME)
        Admin.create(self.cfg.test_dir, None, None, None)
        adm = Admin(Admin.FILENAME)
        self.assertEqual(adm.getWorkflowID(), None)
        ## Created with session info
        os.unlink(Admin.FILENAME)
        Admin.create(self.cfg.test_dir , None, None, None, workflowID=workflowID)
        adm = Admin(Admin.FILENAME)
        self.assertEqual(adm.getWorkflowID(), workflowID)
        ## Missing key
        adm.me.clear()
        self.assertEqual(adm.getWorkflowID(), None)

    def testSession(self):
        adm_session = "adm_dummy"
        ## Created without session info
        os.unlink(Admin.FILENAME)
        Admin.create(self.cfg.test_dir, None, None, None)
        adm = Admin(Admin.FILENAME)
        self.assertEqual(adm.getSession(), None)
        ## Created with session info
        os.unlink(Admin.FILENAME)
        Admin.create(self.cfg.test_dir, None, None, None, sessionID=adm_session)
        adm = Admin(Admin.FILENAME)
        self.assertEqual(adm.getSession(), adm_session)
        ## Missing key
        adm.me.clear()
        self.assertEqual(adm.getSession(), None)


    def testJobName(self):
        adm_jobname = "adm_dummy"
        ## Created without job name info
        os.unlink(Admin.FILENAME)
        Admin.create(self.cfg.test_dir, None, None, None)
        adm = Admin(Admin.FILENAME)
        self.assertEqual(adm.getJobName(), str(None))
        ## Created with job name info
        os.unlink(Admin.FILENAME)
        Admin.create(self.cfg.test_dir, None, adm_jobname, None)
        adm = Admin(Admin.FILENAME)
        self.assertEqual(adm.getJobName(), adm_jobname)
        ## Missing key
        adm.me.clear()
        self.assertEqual(adm.getJobName(), None)

    def testJobID(self):
        adm_jobid = "adm_dummy"
        ## Created without job id info
        os.unlink(Admin.FILENAME)
        Admin.create(self.cfg.test_dir, None, None, None)
        adm = Admin(Admin.FILENAME)
        self.assertEqual(adm.getJobID(), str(None))
        ## Created with job id info
        os.unlink(Admin.FILENAME)
        Admin.create(self.cfg.test_dir, None, None, adm_jobid)
        adm = Admin(Admin.FILENAME)
        self.assertEqual(adm.getJobID(), adm_jobid)
        ## Missing key
        adm.me.clear()
        self.assertEqual(adm.getJobID(), None)

    def testMD5(self):
        adm_md5 = "adm_dummy"
        ## Default
        os.unlink(Admin.FILENAME)
        Admin.create(self.cfg.test_dir, None, None, None)
        adm = Admin(Admin.FILENAME)
        self.assertEqual(adm.getMd5(), None)
        ## Set value
        adm.setMd5(adm_md5)
        self.assertEqual(adm.getMd5(), adm_md5)
        ## Missing key
        adm.me.clear()
        self.assertEqual(adm.getMd5(), None)

    def testExecutionAlias(self):
        adm_executionalias = "adm_dummy"
        ## Default
        os.unlink(Admin.FILENAME)
        Admin.create(self.cfg.test_dir, None, None, None)
        adm = Admin(Admin.FILENAME)
        self.assertEqual(adm.getExecutionAlias(), None)
        ## Set value
        adm.setExecutionAlias(adm_executionalias)
        self.assertEqual(adm.getExecutionAlias(), adm_executionalias)
        ## Missing key
        adm.me.clear()
        self.assertEqual(adm.getExecutionAlias(), None)

    def testQueue(self):
        adm_queue = "adm_dummy"
        ## Default
        os.unlink(Admin.FILENAME)
        Admin.create(self.cfg.test_dir, None, None, None)
        adm = Admin(Admin.FILENAME)
        self.assertEqual(adm.getQueue(), None)
        ## Set value
        adm.setQueue(adm_queue)
        self.assertEqual(adm.getQueue(), adm_queue)
        ## Missing key
        adm.me.clear()
        self.assertEqual(adm.getQueue(), None)

    def testNumber(self):
        adm_number = "adm_dummy"
        ## Default
        os.unlink(Admin.FILENAME)
        Admin.create(self.cfg.test_dir, None, None, None)
        adm = Admin(Admin.FILENAME)
        self.assertEqual(adm.getNumber(), None)
        ## Set value
        adm.setNumber(adm_number)
        self.assertEqual(adm.getNumber(), adm_number)
        ## Missing key
        adm.me.clear()
        self.assertEqual(adm.getNumber(), None)

    def _fakeadmin(self):
        Admin.create(self.cfg.test_dir, None, None, None)
        return Admin(".")

if __name__ == '__main__':
    unittest.main()
