# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.UsingBareVariablesIsDeprecatedRule import UsingBareVariablesIsDeprecatedRule
from ansiblelint.runner import Runner


class TestUsingBareVariablesIsDeprecated(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(UsingBareVariablesIsDeprecatedRule())

    def test_file_positive(self):
        success = 'examples/playbooks/using-bare-variables-success.yml'
        good_runner = Runner(
            success,
            rules=self.collection)
        self.assertEqual([], good_runner.run())

    def test_file_negative(self):
        failure = 'examples/playbooks/using-bare-variables-failure.yml'
        bad_runner = Runner(
            failure,
            rules=self.collection)
        errs = bad_runner.run()
        self.assertEqual(11, len(errs))
