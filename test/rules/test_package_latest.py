"""Tests for package-latest rule."""
from ansiblelint.rules import RulesCollection
from ansiblelint.rules.package_latest import PackageIsNotLatestRule
from ansiblelint.runner import Runner


def test_package_not_latest_positive() -> None:
    """Positive test for package-latest."""
    collection = RulesCollection()
    collection.register(PackageIsNotLatestRule())
    success = "examples/playbooks/package-check-success.yml"
    good_runner = Runner(success, rules=collection)
    assert [] == good_runner.run()


def test_package_not_latest_negative() -> None:
    """Negative test for package-latest."""
    collection = RulesCollection()
    collection.register(PackageIsNotLatestRule())
    failure = "examples/playbooks/package-check-failure.yml"
    bad_runner = Runner(failure, rules=collection)
    errs = bad_runner.run()
    assert len(errs) == 4
