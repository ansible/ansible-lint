import unittest
import ansiblelint.utils
from ansiblelint import RulesCollection
from ansiblelint.rules.EnvVarsInCommandRule import EnvVarsInCommandRule


class TestEnvVarsInCommand(unittest.TestCase):
    collection = RulesCollection()

    def test_file_positive(self):
        self.collection.register(EnvVarsInCommandRule())
        success = 'test/env-vars-in-command-success.yml'
        good_runner = ansiblelint.Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

    def test_file_negative(self):
        self.collection.register(EnvVarsInCommandRule())
        failure = 'test/env-vars-in-command-failure.yml'
        bad_runner = ansiblelint.Runner(self.collection, failure, [], [], [])
        errs = bad_runner.run()
        self.assertEqual(2, len(errs))
