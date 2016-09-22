import unittest
import ansiblelint.utils
from ansiblelint import RulesCollection
from ansiblelint.rules.ShellWithoutPipefail import ShellWithoutPipefail


class TestShellWithoutPipeFail(unittest.TestCase):
    collection = RulesCollection()

    def test_file_positive(self):
        self.collection.register(ShellWithoutPipefail())
        success = 'test/shell-without-pipefail-success.yml'
        good_runner = ansiblelint.Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

    def test_file_negative(self):
        self.collection.register(ShellWithoutPipefail())
        failure = 'test/shell-without-pipefail-failure.yml'
        bad_runner = ansiblelint.Runner(self.collection, failure, [], [], [])
        errs = bad_runner.run()
        self.assertEqual(2, len(errs))
