import pytest

from ansiblelint.runner import Runner


@pytest.mark.parametrize(
    ('filename', 'playbooks_count'),
    (
        pytest.param('blockincludes', 4, id='block included tasks'),
        pytest.param(
            'blockincludes2', 4,
            id='block included tasks with rescue and always',
        ),
        pytest.param('taskincludes', 4, id='included tasks'),
        pytest.param(
            'taskincludes_2_4_style', 4,
            id='include tasks 2.4 style',
        ),
        pytest.param('taskimports', 4, id='import tasks 2 4 style'),
        pytest.param(
            'include-in-block', 3,
            id='include tasks with block include',
        ),
        pytest.param(
            'include-import-tasks-in-role', 4,
            id='include tasks in role',
        ),
    ),
)
def test_included_tasks(default_rules_collection, filename, playbooks_count):
    playbook_path = 'test/{filename}.yml'.format(**locals())
    runner = Runner(default_rules_collection, playbook_path, [], [], [])
    runner.run()
    assert len(runner.playbooks) == playbooks_count
