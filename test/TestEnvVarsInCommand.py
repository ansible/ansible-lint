import unittest
import ansible

from ansiblelint import Runner, RulesCollection
from ansiblelint.rules.EnvVarsInCommandRule import EnvVarsInCommandRule
from pkg_resources import parse_version


class TestEnvVarsInCommand(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(EnvVarsInCommandRule())

    def test_file_positive(self):
        success = 'test/env-vars-in-command-success.yml'
        good_runner = Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

    @unittest.skipIf(parse_version(ansible.__version__) < parse_version('2.4'), "not supported with ansible < 2.4")
    def test_file_positive_2_4(self):
        success = 'test/env-vars-in-command-success_2_4_style.yml'
        good_runner = Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

    def test_file_negative(self):
        failure = 'test/env-vars-in-command-failure.yml'
        bad_runner = Runner(self.collection, failure, [], [], [])
        errs = bad_runner.run()
        self.assertEqual(2, len(errs))
