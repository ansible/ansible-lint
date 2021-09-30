# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.CommandHasChangesCheckRule import CommandHasChangesCheckRule
from ansiblelint.runner import Runner


class TestCommandHasChangesCheck(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self) -> None:
        self.collection.register(CommandHasChangesCheckRule())

    def test_command_changes_positive(self) -> None:
        success = 'examples/playbooks/command-check-success.yml'
        good_runner = Runner(success, rules=self.collection)
        assert [] == good_runner.run()

    def test_command_changes_negative(self) -> None:
        failure = 'examples/playbooks/command-check-failure.yml'
        bad_runner = Runner(failure, rules=self.collection)
        errs = bad_runner.run()
        assert len(errs) == 2
