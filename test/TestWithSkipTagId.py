# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.YamllintRule import YamllintRule
from ansiblelint.runner import Runner


class TestWithSkipTagId(unittest.TestCase):
    collection = RulesCollection()
    collection.register(YamllintRule())
    file = 'examples/playbooks/with-skip-tag-id.yml'

    def test_negative_no_param(self) -> None:
        bad_runner = Runner(self.file, rules=self.collection)
        errs = bad_runner.run()
        assert len(errs) > 0

    def test_negative_with_id(self) -> None:
        with_id = 'yaml'
        bad_runner = Runner(self.file, rules=self.collection, tags=frozenset([with_id]))
        errs = bad_runner.run()
        assert len(errs) > 0

    def test_negative_with_tag(self) -> None:
        with_tag = 'trailing-spaces'
        bad_runner = Runner(
            self.file, rules=self.collection, tags=frozenset([with_tag])
        )
        errs = bad_runner.run()
        assert len(errs) > 0

    def test_positive_skip_id(self) -> None:
        skip_id = 'yaml'
        good_runner = Runner(self.file, rules=self.collection, skip_list=[skip_id])
        assert [] == good_runner.run()

    def test_positive_skip_tag(self) -> None:
        skip_tag = 'trailing-spaces'
        good_runner = Runner(self.file, rules=self.collection, skip_list=[skip_tag])
        assert [] == good_runner.run()
