import unittest
import ansiblelint.utils
from ansiblelint import RulesCollection
from ansiblelint.rules.CommandHasChangesCheckRule import CommandHasChangesCheckRule


class TestCommandHasChangesCheck(unittest.TestCase):
    collection = RulesCollection()

    def test_command_changes_positive(self):
        self.collection.register(CommandHasChangesCheckRule())
        success = 'test/command-check-success.yml'
        good_runner = ansiblelint.Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

    def test_command_changes_negative(self):
        self.collection.register(CommandHasChangesCheckRule())
        failure = 'test/command-check-failure.yml'
        bad_runner = ansiblelint.Runner(self.collection, failure, [], [], [])
        errs = bad_runner.run()
        self.assertEqual(2, len(errs))
