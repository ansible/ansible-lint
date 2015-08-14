import os
import unittest

import ansible.utils

import ansiblelint
from ansiblelint import rules

def runnerFactory(rules, filenames):
    rules_collection = ansiblelint.RulesCollection()
    rules_collection.extend(rules)
    return ansiblelint.Runner(rules_collection, filenames, [], [])

class TestRules(unittest.TestCase):
    def test_git_tasks(self):
        filename = 'test/gittests.txt'
        lint_rules = [rules.GitHasVersionRule.GitHasVersionRule(), ]

        runner = runnerFactory(lint_rules, [filename, ])
        matches = runner.run()
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0].rule.id, 'ANSIBLE0004')
