import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.CommandHasChangesCheckRule import CommandHasChangesCheckRule
from ansiblelint.runner import Runner


class TestCommandHasChangesCheck(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(CommandHasChangesCheckRule())

    def test_command_changes_positive(self):
        success = 'test/command-check-success.yml'
        good_runner = Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

    def test_command_changes_negative(self):
        failure = 'test/command-check-failure.yml'
        bad_runner = Runner(self.collection, failure, [], [], [])
        errs = bad_runner.run()
        self.assertEqual(2, len(errs))
