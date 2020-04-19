import pytest

from ansiblelint import Runner


@pytest.mark.parametrize('stage', ('pre', 'post'))
def test_task_hook_include_playbook(default_rules_collection, stage):
    playbook_path = (
        'test/playbook-include/playbook_{stage}.yml'.
        format_map(locals())
    )
    runner = Runner(default_rules_collection, playbook_path, [], [], [])
    results = runner.run()

    results_text = str(results)
    assert len(runner.playbooks) == 2
    assert len(results) == 3
    assert 'Commands should not change things' in results_text
    assert '502' not in results_text
    assert 'All tasks should be named' not in results_text
