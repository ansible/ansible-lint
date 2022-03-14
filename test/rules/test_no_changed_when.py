"""Tests for no-change-when rule."""
from ansiblelint.rules import RulesCollection
from ansiblelint.rules.no_changed_when import CommandHasChangesCheckRule
from ansiblelint.runner import Runner


def test_command_changes_positive() -> None:
    """Positive test for no-changed-when."""
    collection = RulesCollection()
    collection.register(CommandHasChangesCheckRule())
    success = "examples/playbooks/command-check-success.yml"
    good_runner = Runner(success, rules=collection)
    assert [] == good_runner.run()


def test_command_changes_negative() -> None:
    """Negative test for no-changed-when."""
    collection = RulesCollection()
    collection.register(CommandHasChangesCheckRule())
    failure = "examples/playbooks/command-check-failure.yml"
    bad_runner = Runner(failure, rules=collection)
    errs = bad_runner.run()
    assert len(errs) == 2
