import unittest

from ansiblelint import AnsibleLintRule
from ansiblelint import RulesCollection

class TestRulesCollection(unittest.TestCase):

    rules = None

    def setUp(self):
        self.rules = RulesCollection.create_from_directory('./test/rules')

    def test_load_collection_from_directory(self):
        self.assertEqual(len(self.rules), 2)

    def test_run_collection(self):
        matches = self.rules.run('test/ematchtest.txt')
        self.assertEqual(len(matches), 3)

    def test_tags(self):
        matches = self.rules.run('test/ematchtest.txt', tags=['test1'])
        self.assertEqual(len(matches), 3)
        matches = self.rules.run('test/ematchtest.txt', tags=['test2'])
        self.assertEqual(len(matches), 0)
        matches = self.rules.run('test/bracketsmatchtest.txt', tags=['test1'])
        self.assertEqual(len(matches), 1)
        matches = self.rules.run('test/bracketsmatchtest.txt', tags=['test2'])
        self.assertEqual(len(matches), 2)
         
         

    def test_skip_tags(self):
        matches = self.rules.run('test/ematchtest.txt', skip_tags=['test1'])
        self.assertEqual(len(matches), 0)
        matches = self.rules.run('test/ematchtest.txt', skip_tags=['test2'])
        self.assertEqual(len(matches), 3)
        matches = self.rules.run('test/bracketsmatchtest.txt', skip_tags=['test1'])
        self.assertEqual(len(matches), 2)
        matches = self.rules.run('test/bracketsmatchtest.txt', skip_tags=['test2'])
        self.assertEqual(len(matches), 1)

   
