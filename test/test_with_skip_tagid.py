"""Tests related to skip tag id."""

import pytest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.yaml_rule import YamllintRule
from ansiblelint.runner import Runner
from ansiblelint.testing import run_ansible_lint

FILE = "examples/playbooks/with-skip-tag-id.yml"


@pytest.fixture(name="collection")
def fixture_collection(empty_rule_collection: RulesCollection) -> RulesCollection:
    """Create a rules collection with YamllintRule registered."""
    empty_rule_collection.register(YamllintRule())
    return empty_rule_collection


def test_negative_no_param(collection: RulesCollection) -> None:
    """Negative test no param."""
    bad_runner = Runner(FILE, rules=collection)
    errs = bad_runner.run()
    assert len(errs) > 0


def test_negative_with_id(collection: RulesCollection) -> None:
    """Negative test with_id."""
    with_id = "yaml"
    bad_runner = Runner(FILE, rules=collection, tags=frozenset([with_id]))
    errs = bad_runner.run()
    assert len(errs) == 1


def test_negative_with_tag(collection: RulesCollection) -> None:
    """Negative test with_tag."""
    with_tag = "yaml[trailing-spaces]"
    bad_runner = Runner(FILE, rules=collection, tags=frozenset([with_tag]))
    errs = bad_runner.run()
    assert len(errs) == 1


def test_positive_skip_id(collection: RulesCollection) -> None:
    """Positive test skip_id."""
    skip_id = "yaml"
    good_runner = Runner(FILE, rules=collection, skip_list=[skip_id])
    assert good_runner.run() == []


def test_positive_skip_id_2(collection: RulesCollection) -> None:
    """Positive test skip_id."""
    skip_id = "key-order"
    good_runner = Runner(FILE, rules=collection, tags=frozenset([skip_id]))
    assert good_runner.run() == []


def test_positive_skip_tag(collection: RulesCollection) -> None:
    """Positive test skip_tag."""
    skip_tag = "yaml[trailing-spaces]"
    good_runner = Runner(FILE, rules=collection, skip_list=[skip_tag])
    assert good_runner.run() == []


def test_run_skip_rule() -> None:
    """Test that we can skip a rule with -x."""
    result = run_ansible_lint(
        "-x",
        "name[casing]",
        "examples/playbooks/rule-name-casing.yml",
        executable="ansible-lint",
    )
    assert result.returncode == 0
    assert not result.stdout
