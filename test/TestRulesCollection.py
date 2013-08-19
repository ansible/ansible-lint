import unittest

from ansiblelint import AnsibleLintRule
from ansiblelint import RulesCollection

class TestRulesCollection(unittest.TestCase):

    def test_add_two_rules(self):
        rules = RulesCollection()
        self.assertEqual(len(rules), 0)
        rule1 = AnsibleLintRule(id='RULE1', description='rule1')
        rules.register(rule1)
        rule2 = AnsibleLintRule(id='RULE2', description='rule2')
        rules.register(rule2)
        self.assertEqual(len(rules), 2)

    def test_load_collection_from_directory(self):
        rules = RulesCollection.create_from_directory('./test/rules')
        self.assertEqual(len(rules), 1)
