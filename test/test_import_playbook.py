"""Test ability to import playbooks."""

from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner


def test_task_hook_import_playbook(default_rules_collection: RulesCollection) -> None:
    """Assures import_playbook includes are recognized."""
    playbook_path = "examples/playbooks/playbook-parent.yml"
    runner = Runner(playbook_path, rules=default_rules_collection)
    results = runner.run()

    results_text = str(results)
    assert len(runner.lintables) == 2
    assert len(results) == 2
    # Assures we detected the issues from imported playbook
    assert "Commands should not change things" in results_text
    assert "[name]" in results_text
    assert "All tasks should be named" in results_text


def test_import_playbook_from_collection(
    default_rules_collection: RulesCollection,
) -> None:
    """Assures import_playbook from collection."""
    playbook_path = "examples/playbooks/test_import_playbook.yml"
    runner = Runner(playbook_path, rules=default_rules_collection)
    results = runner.run()

    assert len(runner.lintables) == 1
    assert len(results) == 0


def test_import_playbook_invalid(
    default_rules_collection: RulesCollection,
) -> None:
    """Assures import_playbook from collection."""
    playbook_path = "examples/playbooks/test_import_playbook_invalid.yml"
    runner = Runner(playbook_path, rules=default_rules_collection)
    results = runner.run()

    assert len(runner.lintables) == 1
    assert len(results) == 1
    assert results[0].tag == "syntax-check[specific]"
    assert results[0].lineno == 2
