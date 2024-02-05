"""Tests for LoadFailureRule."""

import pytest

from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner


@pytest.mark.parametrize(
    "path",
    (
        pytest.param("examples/broken/encoding.j2", id="jinja2"),
        pytest.param("examples/broken/encoding.yml", id="yaml"),
    ),
)
def test_load_failure_encoding(
    path: str,
    default_rules_collection: RulesCollection,
) -> None:
    """Check that we fail when file encoding is wrong."""
    runner = Runner(path, rules=default_rules_collection)
    matches = runner.run()
    assert len(matches) == 1, matches
    assert matches[0].rule.id == "load-failure"
    assert "'utf-8' codec can't decode byte" in matches[0].message
    assert matches[0].tag == "load-failure[unicodedecodeerror]"
