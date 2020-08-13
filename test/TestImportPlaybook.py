"""Test ability to import playbooks."""
from ansiblelint.runner import Runner


def test_task_hook_import_playbook(default_rules_collection):
    """Assures import_playbook includes are recognized."""
    playbook_path = 'test/playbook-import/playbook_parent.yml'
    runner = Runner(default_rules_collection, playbook_path, [], [], [])
    results = runner.run()

    results_text = str(results)
    assert len(runner.playbooks) == 2
    assert len(results) == 2
    # Assures we detected the issues from imported playbook
    assert 'Commands should not change things' in results_text
    assert '502' in results_text
    assert 'All tasks should be named' in results_text
