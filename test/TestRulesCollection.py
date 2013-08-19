import unittest

from ansiblelint import AnsibleLintRule
from ansiblelint import RulesCollection

class TestRulesCollection(unittest.TestCase):

    rules = None
    
    def setUp(self):
        self.rules = RulesCollection()

    def test_add_two_rules(self):
        self.assertEqual(len(self.rules), 0)
        rule1 = AnsibleLintRule(id='RULE1', description='rule1')
        self.rules.register(rule1)
        rule2 = AnsibleLintRule(id='RULE2', description='rule2')
        self.rules.register(rule2)
        self.assertEqual(len(self.rules), 2)

