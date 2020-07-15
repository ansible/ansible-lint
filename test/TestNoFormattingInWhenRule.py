import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.NoFormattingInWhenRule import NoFormattingInWhenRule
from ansiblelint.runner import Runner


class TestNoFormattingInWhenRule(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(NoFormattingInWhenRule())

    def test_file_positive(self):
        success = 'test/jinja2-when-success.yml'
        good_runner = Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

    def test_file_negative(self):
        failure = 'test/jinja2-when-failure.yml'
        bad_runner = Runner(self.collection, failure, [], [], [])
        errs = bad_runner.run()
        self.assertEqual(2, len(errs))
