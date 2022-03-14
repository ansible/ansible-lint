"""Tests for deprecated-bare-vars rule."""
from ansiblelint.rules import RulesCollection
from ansiblelint.rules.deprecated_bare_vars import UsingBareVariablesIsDeprecatedRule
from ansiblelint.runner import Runner


def test_use_bare_positive() -> None:
    """Positive test for deprecated-bare-vars."""
    collection = RulesCollection()
    collection.register(UsingBareVariablesIsDeprecatedRule())
    success = "examples/playbooks/using-bare-variables-success.yml"
    good_runner = Runner(success, rules=collection)
    assert [] == good_runner.run()


def test_use_bare_negative() -> None:
    """Negative test for deprecated-bare-vars."""
    collection = RulesCollection()
    collection.register(UsingBareVariablesIsDeprecatedRule())
    failure = "examples/playbooks/using-bare-variables-failure.yml"
    bad_runner = Runner(failure, rules=collection)
    errs = bad_runner.run()
    assert len(errs) == 11
