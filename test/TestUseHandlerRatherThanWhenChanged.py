import unittest
from ansiblelint import RulesCollection, Runner
from ansiblelint.rules.UseHandlerRatherThanWhenChangedRule import UseHandlerRatherThanWhenChangedRule


class TestUseHandlerRatherThanWhenChanged(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(UseHandlerRatherThanWhenChangedRule())

    def test_file_positive(self):
        success = 'test/use-handler-rather-than-when-changed-success.yml'
        good_runner = Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

    def test_file_negative(self):
        failure = 'test/use-handler-rather-than-when-changed-failure.yml'
        bad_runner = Runner(self.collection, failure, [], [], [])
        errs = bad_runner.run()
        self.assertEqual(5, len(errs))
