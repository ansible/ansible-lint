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
