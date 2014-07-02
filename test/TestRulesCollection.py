import unittest

from ansiblelint import AnsibleLintRule
from ansiblelint import RulesCollection

class TestRulesCollection(unittest.TestCase):

    rules = None
    ematchtestfile = dict(path='test/ematchtest.txt',type='playbook')
    bracketsmatchtestfile = dict(path='test/bracketsmatchtest.txt',type='playbook')

    def setUp(self):
        self.rules = RulesCollection.create_from_directory('./test/rules')

    def test_load_collection_from_directory(self):
        self.assertEqual(len(self.rules), 2)

    def test_run_collection(self):
        matches = self.rules.run(self.ematchtestfile)
        self.assertEqual(len(matches), 3)

    def test_tags(self):
        matches = self.rules.run(self.ematchtestfile, tags=['test1'])
        self.assertEqual(len(matches), 3)
        matches = self.rules.run(self.ematchtestfile, tags=['test2'])
        self.assertEqual(len(matches), 0)
        matches = self.rules.run(self.bracketsmatchtestfile, tags=['test1'])
        self.assertEqual(len(matches), 1)
        matches = self.rules.run(self.bracketsmatchtestfile, tags=['test2'])
        self.assertEqual(len(matches), 2)
         
         

    def test_skip_tags(self):
        matches = self.rules.run(self.ematchtestfile, skip_tags=['test1'])
        self.assertEqual(len(matches), 0)
        matches = self.rules.run(self.ematchtestfile, skip_tags=['test2'])
        self.assertEqual(len(matches), 3)
        matches = self.rules.run(self.bracketsmatchtestfile, skip_tags=['test1'])
        self.assertEqual(len(matches), 2)
        matches = self.rules.run(self.bracketsmatchtestfile, skip_tags=['test2'])
        self.assertEqual(len(matches), 1)

   
