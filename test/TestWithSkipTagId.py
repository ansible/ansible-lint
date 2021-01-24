# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.YamllintRule import YamllintRule
from ansiblelint.runner import Runner


class TestWithSkipTagId(unittest.TestCase):
    collection = RulesCollection()
    collection.register(YamllintRule())
    file = 'test/with-skip-tag-id.yml'

    def test_negative_no_param(self) -> None:
        bad_runner = Runner(
            self.file,
            rules=self.collection)
        errs = bad_runner.run()
        self.assertGreater(len(errs), 0)

    def test_negative_with_id(self) -> None:
        with_id = 'YAML'
        bad_runner = Runner(
            self.file,
            rules=self.collection,
            tags=frozenset([with_id]))
        errs = bad_runner.run()
        self.assertGreater(len(errs), 0)

    def test_negative_with_tag(self) -> None:
        with_tag = 'formatting'
        bad_runner = Runner(
            self.file,
            rules=self.collection,
            tags=frozenset([with_tag]))
        errs = bad_runner.run()
        self.assertGreater(len(errs), 0)

    def test_positive_skip_id(self) -> None:
        skip_id = 'YAML'
        good_runner = Runner(
            self.file,
            rules=self.collection,
            skip_list=[skip_id])
        self.assertEqual([], good_runner.run())

    def test_positive_skip_tag(self) -> None:
        skip_tag = 'formatting'
        good_runner = Runner(
            self.file,
            rules=self.collection,
            skip_list=[skip_tag])
        self.assertEqual([], good_runner.run())
