"""Test related to import of invalid files."""
import pytest

from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner


@pytest.mark.parametrize(
    "playbook_path",
    (
        pytest.param(
            "examples/playbooks/test_import_with_conflicting_action_statements.yml",
            id="0",
        ),
        pytest.param("examples/playbooks/test_import_with_malformed.yml", id="1"),
    ),
)
def test_import_tasks(
    default_rules_collection: RulesCollection, playbook_path: str
) -> None:
    """Assures import_playbook includes are recognized."""
    runner = Runner(playbook_path, rules=default_rules_collection)
    results = runner.run()

    assert len(runner.lintables) == 1
    assert len(results) == 1
    # Assures we detected the issues from imported file
    assert results[0].rule.id == "syntax-check"
