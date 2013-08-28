import unittest

import ansiblelint.utils
from ansiblelint import AnsibleLintRule
from rules import EMatcherRule, UnsetVariableMatcherRule


class TestRule(unittest.TestCase):

    def test_rule_matching(self):
        text = ""
        filename = 'test/ematchtest.txt'
        with open(filename) as f:
            text = f.read()
        ematcher = EMatcherRule.EMatcherRule()
        matches = ematcher.matchlines(filename, text)
        self.assertEqual(len(matches), 3)

    def test_rule_postmatching(self):
        text = ""
        filename = 'test/bracketsmatchtest.txt'
        with open(filename) as f:
            text = f.read()
        rule = UnsetVariableMatcherRule.UnsetVariableMatcherRule()
        matches = rule.matchlines(filename, text)
        self.assertEqual(len(matches), 2)
