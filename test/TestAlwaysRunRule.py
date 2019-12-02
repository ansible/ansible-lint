import unittest

from ansible import __version__ as ANSIBLE_VERSION
from ansiblelint import RulesCollection, Runner
from ansiblelint.rules.AlwaysRunRule import AlwaysRunRule
import semver


class TestAlwaysRun(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(AlwaysRunRule())

    @unittest.skipIf(semver.match(ANSIBLE_VERSION, '>=2.7.0'),
                     "'always_run' not supported in this ansible version range")
    def test_file_positive(self):
        success = 'test/always-run-success.yml'
        good_runner = Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

    @unittest.skipIf(semver.match(ANSIBLE_VERSION, '>=2.7.0'),
                     "'always_run' not supported in this ansible version range")
    def test_file_negative(self):
        failure = 'test/always-run-failure.yml'
        bad_runner = Runner(self.collection, failure, [], [], [])
        errs = bad_runner.run()
        self.assertEqual(1, len(errs))
