import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.AlwaysRunRule import AlwaysRunRule
from ansiblelint.runner import Runner


class TestAlwaysRun(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(AlwaysRunRule())

    def test_file_positive(self):
        success = 'test/always-run-success.yml'
        good_runner = Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

    def test_file_negative(self):
        failure = 'test/always-run-failure.yml'
        bad_runner = Runner(self.collection, failure, [], [], [])
        errs = bad_runner.run()
        self.assertEqual(1, len(errs))
