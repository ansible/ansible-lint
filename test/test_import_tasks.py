"""Test related to import of invalid files."""

import pytest

from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner


@pytest.mark.parametrize(
    ("playbook_path", "lintable_count", "match_count"),
    (
        pytest.param(
            "examples/playbooks/test_import_with_conflicting_action_statements.yml",
            2,
            4,
            id="0",
        ),
        pytest.param("examples/playbooks/test_import_with_malformed.yml", 2, 2, id="1"),
    ),
)
def test_import_tasks(
    default_rules_collection: RulesCollection,
    playbook_path: str,
    lintable_count: int,
    match_count: int,
) -> None:
    """Assures import_playbook includes are recognized."""
    runner = Runner(playbook_path, rules=default_rules_collection)
    results = runner.run()

    assert len(runner.lintables) == lintable_count
    assert len(results) == match_count
    # Assures we detected the issues from imported file
    assert results[0].rule.id in ("syntax-check", "load-failure")
