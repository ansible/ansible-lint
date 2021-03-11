# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.CommandsInsteadOfModulesRule import CommandsInsteadOfModulesRule
from ansiblelint.runner import Runner


class TestCommandsInsteadOfModulesRule(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(CommandsInsteadOfModulesRule())

    def test_file_positive(self):
        success = 'examples/playbooks/commands-instead-of-modules-success.yml'
        good_runner = Runner(success, rules=self.collection)
        self.assertEqual([], good_runner.run())

    def test_file_negative(self):
        failure = 'examples/playbooks/commands-instead-of-modules-failure.yml'
        bad_runner = Runner(failure, rules=self.collection)
        errs = bad_runner.run()
        self.assertEqual(3, len(errs))
