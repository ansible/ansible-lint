import unittest
import ansiblelint.utils
from ansiblelint import RulesCollection
from ansiblelint.rules.UsingBareVariablesIsDeprecatedRule import UsingBareVariablesIsDeprecatedRule


class TestUsingBareVariablesIsDeprecated(unittest.TestCase):
    collection = RulesCollection()

    def test_file_positive(self):
        self.collection.register(UsingBareVariablesIsDeprecatedRule())
        success = 'test/using-bare-variables-success.yml'
        good_runner = ansiblelint.Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

    def test_file_negative(self):
        self.collection.register(UsingBareVariablesIsDeprecatedRule())
        failure = 'test/using-bare-variables-failure.yml'
        bad_runner = ansiblelint.Runner(self.collection, failure, [], [], [])
        errs = bad_runner.run()
        self.assertEqual(12, len(errs))
