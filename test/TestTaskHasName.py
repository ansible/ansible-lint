# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.TaskHasNameRule import TaskHasNameRule
from ansiblelint.runner import Runner


class TestTaskHasNameRule(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self) -> None:
        self.collection.register(TaskHasNameRule())

    def test_file_positive(self) -> None:
        success = 'examples/playbooks/task-has-name-success.yml'
        good_runner = Runner(success, rules=self.collection)
        assert [] == good_runner.run()

    def test_file_negative(self) -> None:
        failure = 'examples/playbooks/task-has-name-failure.yml'
        bad_runner = Runner(failure, rules=self.collection)
        errs = bad_runner.run()
        assert len(errs) == 4
