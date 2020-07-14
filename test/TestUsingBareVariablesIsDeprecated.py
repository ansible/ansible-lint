import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.UsingBareVariablesIsDeprecatedRule import UsingBareVariablesIsDeprecatedRule
from ansiblelint.runner import Runner


class TestUsingBareVariablesIsDeprecated(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(UsingBareVariablesIsDeprecatedRule())

    def test_file_positive(self):
        success = 'test/using-bare-variables-success.yml'
        good_runner = Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

    def test_file_negative(self):
        failure = 'test/using-bare-variables-failure.yml'
        bad_runner = Runner(self.collection, failure, [], [], [])
        errs = bad_runner.run()
        self.assertEqual(14, len(errs))
