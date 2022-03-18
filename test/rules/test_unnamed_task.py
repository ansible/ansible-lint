"""Tests for unnamed-task rule."""
from ansiblelint.rules import RulesCollection
from ansiblelint.rules.unnamed_task import TaskHasNameRule
from ansiblelint.runner import Runner


def test_file_positive() -> None:
    """Positive test for unnamed-task."""
    collection = RulesCollection()
    collection.register(TaskHasNameRule())
    success = "examples/playbooks/task-has-name-success.yml"
    good_runner = Runner(success, rules=collection)
    assert [] == good_runner.run()


def test_file_negative() -> None:
    """Negative test for unnamed-task."""
    collection = RulesCollection()
    collection.register(TaskHasNameRule())
    failure = "examples/playbooks/task-has-name-failure.yml"
    bad_runner = Runner(failure, rules=collection)
    errs = bad_runner.run()
    assert len(errs) == 4
