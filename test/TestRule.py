import unittest

from ansiblelint import AnsibleLintRule
from ansiblelint import RulesCollection

class TestRule(unittest.TestCase):

    def tearDown(self):
        RulesCollection.resetInstance()

    def test_add_two_rules(self):
        self.assertEqual(len(RulesCollection.getInstance()), 0)
        rule1 = AnsibleLintRule(id='RULE1', description='rule1')
        RulesCollection.register(rule1)
        rule2 = AnsibleLintRule(id='RULE2', description='rule2')
        RulesCollection.register(rule2)
        self.assertEqual(len(RulesCollection.getInstance()), 2)

    def test_add_different_two_rules(self):
        self.assertEqual(len(RulesCollection.getInstance()), 0)
        rule3 = AnsibleLintRule(id='RULE3', description='rule3')
        RulesCollection.register(rule3)
        rule4 = AnsibleLintRule(id='RULE4', description='rule4')
        RulesCollection.register(rule4)
        self.assertEqual(len(RulesCollection.getInstance()), 2)
