from GangaTest.Framework.tests import GangaGPITestCase

from GangaTest.Framework.utils import sleep_until_completed,file_contains,write_file,sleep_until_state
from GangaLHCb.test import *
addDiracTestSubmitter()


class TestRootDirac(GangaGPITestCase):


    def testAllowedArchitecture(self):
        """Test the submission of root jobs on dirac"""
        
        config.ROOT.arch = 'slc4_ia32_gcc34'
        
        r = Root()
        r.usepython = False

        j = Job(application=r, backend=TestSubmitter())
        j.submit()
        sleep_until_completed(j)
        assert j.status == 'completed', 'Job should complete'
        
    def testNotAllowedArchitecture(self):
        """Tests the architectures not allowed by dirac"""

        config.ROOT.arch = 'slc4_ia32_gcc34-not-a-valid-version'
        
        r = Root()
        r.usepython = False

        j = Job(application=r, backend=TestSubmitter())
        
        try:
            j.submit()
            assert False, 'Exception must be thrown'
        except JobError, e:
            pass
        
        assert j.status == 'new', 'Job must be rolled back to the new state'
        
    def testProperSubmit(self):
        
        config.ROOT.arch = 'slc4_ia32_gcc34'
        
        j = Job(application=Root(), backend=Dirac())
        j.submit()
        
        sleep_until_state(j, state = 'submitted')
        assert j.status == 'submitted', 'Job should submit'
        j.kill()
        