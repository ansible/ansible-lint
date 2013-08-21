import unittest

import ansiblelint.utils
from ansiblelint import AnsibleLintRule
from rules import EMatcherRule, UnsetVariableMatcherRule


class TestRule(unittest.TestCase):

    def test_rule_matching(self):
        text = ""
        with open('test/ematchtest.txt') as f:
            text = f.read()
        ematcher = EMatcherRule.EMatcherRule()
        linenos = ematcher.prematch(text)
        self.assertEqual(linenos, [1,3,5])

    def test_rule_postmatching(self):
        text = ""
        with open('test/bracketsmatchtest.txt') as f:
            text = f.read()
        rule = UnsetVariableMatcherRule.UnsetVariableMatcherRule()
        linenos = rule.postmatch(text)
        self.assertEqual(linenos, [1,3])
