"""Tests for partial-become rule."""
from ansiblelint.rules import RulesCollection
from ansiblelint.rules.partial_become import BecomeUserWithoutBecomeRule
from ansiblelint.runner import Runner


def test_file_positive() -> None:
    """Positive test for partial-become."""
    collection = RulesCollection()
    collection.register(BecomeUserWithoutBecomeRule())
    success = "examples/playbooks/become-user-without-become-success.yml"
    good_runner = Runner(success, rules=collection)
    assert [] == good_runner.run()


def test_file_negative() -> None:
    """Negative test for partial-become."""
    collection = RulesCollection()
    collection.register(BecomeUserWithoutBecomeRule())
    failure = "examples/playbooks/become-user-without-become-failure.yml"
    bad_runner = Runner(failure, rules=collection)
    errs = bad_runner.run()
    assert len(errs) == 3
