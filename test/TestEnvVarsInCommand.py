import unittest
from ansiblelint import Runner, RulesCollection
from ansiblelint.rules.EnvVarsInCommandRule import EnvVarsInCommandRule


class TestEnvVarsInCommand(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(EnvVarsInCommandRule())

    def test_file_positive(self):
        success = 'test/env-vars-in-command-success.yml'
        good_runner = Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

    def test_file_negative(self):
        failure = 'test/env-vars-in-command-failure.yml'
        bad_runner = Runner(self.collection, failure, [], [], [])
        errs = bad_runner.run()
        self.assertEqual(2, len(errs))
