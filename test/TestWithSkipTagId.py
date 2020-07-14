import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.TrailingWhitespaceRule import TrailingWhitespaceRule
from ansiblelint.runner import Runner


class TestWithSkipTagId(unittest.TestCase):
    collection = RulesCollection()
    collection.register(TrailingWhitespaceRule())
    file = 'test/with-skip-tag-id.yml'

    def test_negative_no_param(self):
        bad_runner = Runner(self.collection, self.file, [], [], [])
        errs = bad_runner.run()
        self.assertGreater(len(errs), 0)

    def test_negative_with_id(self):
        with_id = '201'
        bad_runner = Runner(self.collection, self.file, [with_id], [], [])
        errs = bad_runner.run()
        self.assertGreater(len(errs), 0)

    def test_negative_with_tag(self):
        with_tag = 'ANSIBLE0002'
        bad_runner = Runner(self.collection, self.file, [with_tag], [], [])
        errs = bad_runner.run()
        self.assertGreater(len(errs), 0)

    def test_positive_skip_id(self):
        skip_id = '201'
        good_runner = Runner(self.collection, self.file, [], [skip_id], [])
        self.assertEqual([], good_runner.run())

    def test_positive_skip_tag(self):
        skip_tag = 'ANSIBLE0002'
        good_runner = Runner(self.collection, self.file, [], [skip_tag], [])
        self.assertEqual([], good_runner.run())
