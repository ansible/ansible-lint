# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.UseCommandInsteadOfShellRule import UseCommandInsteadOfShellRule
from ansiblelint.runner import Runner


class TestUseCommandInsteadOfShell(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(UseCommandInsteadOfShellRule())

    def test_file_positive(self):
        success = 'examples/playbooks/command-instead-of-shell-success.yml'
        good_runner = Runner(success, rules=self.collection)
        self.assertEqual([], good_runner.run())

    def test_file_negative(self):
        failure = 'examples/playbooks/command-instead-of-shell-failure.yml'
        bad_runner = Runner(failure, rules=self.collection)
        errs = bad_runner.run()
        self.assertEqual(2, len(errs))
