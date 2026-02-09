"""Tests for package-latest rule."""

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.package_latest import PackageIsNotLatestRule
from ansiblelint.runner import Runner


def test_package_not_latest_positive(empty_rule_collection: RulesCollection) -> None:
    """Positive test for package-latest."""
    empty_rule_collection.register(PackageIsNotLatestRule())
    success = "examples/playbooks/package-check-success.yml"
    good_runner = Runner(success, rules=empty_rule_collection)
    assert good_runner.run() == []


def test_package_not_latest_negative(empty_rule_collection: RulesCollection) -> None:
    """Negative test for package-latest."""
    empty_rule_collection.register(PackageIsNotLatestRule())
    failure = "examples/playbooks/package-check-failure.yml"
    bad_runner = Runner(failure, rules=empty_rule_collection)
    errs = bad_runner.run()
    assert len(errs) == 5
