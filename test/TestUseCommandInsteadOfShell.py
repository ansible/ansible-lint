import unittest
import ansiblelint.utils
from ansiblelint import RulesCollection
from ansiblelint.rules.UseCommandInsteadOfShellRule import UseCommandInsteadOfShellRule


class TestUseCommandInsteadOfShell(unittest.TestCase):
    collection = RulesCollection()

    def test_file_positive(self):
        self.collection.register(UseCommandInsteadOfShellRule())
        success = 'test/command-instead-of-shell-success.yml'
        good_runner = ansiblelint.Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

    def test_file_negative(self):
        self.collection.register(UseCommandInsteadOfShellRule())
        failure = 'test/command-instead-of-shell-failure.yml'
        bad_runner = ansiblelint.Runner(self.collection, failure, [], [], [])
        errs = bad_runner.run()
        self.assertEqual(3, len(errs))
