# -*- encoding: utf-8 -*-
from __future__ import with_statement
import sys, os, unittest, tempfile, shutil
from copy import copy

DATA1 = "tjosan"
DATA1_MD5 = "5558e0551622725a5fa380caffa94c5d"
DATA2 = "tjosan hejsan"
DATA2_MD5 = "923574a1a36aebc7e1f586b7d363005e"

TMPDIR=tempfile.gettempdir()

if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import workdir
from blobrepo import repository
from common import get_tree

class WorkdirHelper:
    def mkdir(self, path):
        assert not os.path.isabs(path)
        dirpath = os.path.join(self.workdir, path)
        os.makedirs(dirpath)

    def addWorkdirFile(self, path, content):
        assert not os.path.isabs(path)
        filepath = os.path.join(self.workdir, path)
        with open(filepath, "w") as f:
            f.write(content)
    
    def rmWorkdirFile(self, path):
        assert not os.path.isabs(path)
        filepath = os.path.join(self.workdir, path)
        os.unlink(filepath)

    def createTmpName(self, suffix = ""):
        filename = tempfile.mktemp(prefix='testworkdir'+suffix+"_", dir=TMPDIR)
        self.remove_at_teardown.append(filename)
        return filename

    def assertContents(self, path, expected_contents):
        with open(path, "rb") as f:
            file_contents = f.read()
            self.assertEquals(file_contents, expected_contents)
        

class TestWorkdir(unittest.TestCase, WorkdirHelper):
    def setUp(self):
        self.remove_at_teardown = []
        self.workdir = self.createTmpName()
        self.repopath = self.createTmpName()
        repository.create_repository(self.repopath)
        os.mkdir(self.workdir)
        self.wd = workdir.Workdir(self.repopath, "TestSession", "", None, self.workdir)
        id = self.wd.checkin()
        assert id == 1

    def tearDown(self):
        for d in self.remove_at_teardown:
            shutil.rmtree(d, ignore_errors = True)

    #
    # Actual tests start here
    #

    def testEmpty(self):
        changes = self.wd.get_changes()
        self.assertEqual(changes, ([], [], [], [], []))

    def testGetChangesUnversionedFile(self):
        # Test unversioned file
        self.addWorkdirFile("tjosan.txt", "tjosanhejsan")
        changes = self.wd.get_changes()
        self.assertEqual(changes, ([], ["tjosan.txt"], [], [], []))

    def testGetChangesUnchangedFile(self):        
        self.addWorkdirFile("tjosan.txt", "tjosanhejsan")
        self.wd.checkin()
        changes = self.wd.get_changes()
        self.assertEqual(changes, (["tjosan.txt"], [], [], [], []))

    def testGetChangesUnchangedFileWithFunkyName(self):        
        name = "Tjosan_räk smörgås.txt"
        self.addWorkdirFile(name, "tjosanhejsan")
        self.wd.checkin()
        changes = self.wd.get_changes()
        self.assertEqual(changes, ([name], [], [], [], []))

    def testGetChangesMissingFile(self):
        self.addWorkdirFile("tjosan.txt", "tjosanhejsan")
        self.wd.checkin()
        self.rmWorkdirFile("tjosan.txt")
        changes = self.wd.get_changes()
        self.assertEqual(changes, ([], [], [], ["tjosan.txt"], []))

    def testGetChangesUnchangedFileSubdir(self):
        self.mkdir("subdir")
        self.addWorkdirFile("subdir/tjosan.txt", "tjosanhejsan")
        self.wd.checkin()
        changes = self.wd.get_changes()
        self.assertEqual(changes, (["subdir/tjosan.txt"], [], [], [], []))

    def testTwoNewIdenticalFiles(self):
        self.mkdir("subdir")
        self.addWorkdirFile("subdir/tjosan1.txt", "tjosanhejsan")
        self.addWorkdirFile("subdir/tjosan2.txt", "tjosanhejsan")
        self.wd.checkin()
        changes = self.wd.get_changes()
        # Order doesnt matter below really, so this is fragile
        self.assertEqual(changes, (["subdir/tjosan2.txt", "subdir/tjosan1.txt"], [], [], [], []))


class TestPartialCheckin(unittest.TestCase, WorkdirHelper):
    def setUp(self):
        self.remove_at_teardown = []
        self.workdir = self.createTmpName("_wd")
        self.repopath = self.createTmpName("_repo")
        repository.create_repository(self.repopath)

    def createTestRepo(self):
        os.mkdir(self.workdir)
        wd = workdir.Workdir(self.repopath, "TestSession", "", None, self.workdir)
        self.addWorkdirFile("onlyintopdir.txt", "nothing")
        self.mkdir("mysubdir")
        self.addWorkdirFile("mysubdir/insubdir.txt", "nothing2")
        id = wd.checkin()
        assert id == 1
        shutil.rmtree(self.workdir, ignore_errors = True)

    def tearDown(self):
        for d in self.remove_at_teardown:
            shutil.rmtree(d, ignore_errors = True)

    def testPartialCheckout(self):
        self.createTestRepo()
        os.mkdir(self.workdir)
        wd = workdir.Workdir(self.repopath, "TestSession", "mysubdir", None, self.workdir)
        wd.checkout()
        tree = get_tree(wd.root, absolute_paths = False)
        #tree = wd.get_tree(absolute_paths = True)
        self.assertEquals(set(tree), set(["insubdir.txt", '.meta/info']))

if __name__ == '__main__':
    unittest.main()
