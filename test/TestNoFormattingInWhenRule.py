# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.NoFormattingInWhenRule import NoFormattingInWhenRule
from ansiblelint.runner import Runner


class TestNoFormattingInWhenRule(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(NoFormattingInWhenRule())

    def test_file_positive(self):
        success = 'examples/playbooks/jinja2-when-success.yml'
        good_runner = Runner(
            success,
            rules=self.collection)
        self.assertEqual([], good_runner.run())

    def test_file_negative(self):
        failure = 'examples/playbooks/jinja2-when-failure.yml'
        bad_runner = Runner(
            failure,
            rules=self.collection)
        errs = bad_runner.run()
        self.assertEqual(2, len(errs))
