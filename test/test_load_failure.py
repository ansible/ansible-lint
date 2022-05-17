"""Tests for LoadFailureRule."""
from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner


def test_load_failure_encoding(default_rules_collection: RulesCollection) -> None:
    """Check that we fail when file encoding is wrong."""
    runner = Runner("examples/broken/encoding.j2", rules=default_rules_collection)
    matches = runner.run()
    assert len(matches) == 1, matches
    assert matches[0].rule.id == "load-failure"
    assert "'utf-8' codec can't decode byte" in matches[0].message
    assert matches[0].tag == "load-failure[unicodedecodeerror]"
