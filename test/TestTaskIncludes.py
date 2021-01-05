import pytest

from ansiblelint.file_utils import Lintable
from ansiblelint.runner import Runner


@pytest.mark.parametrize(
    ('filename', 'file_count', "match_count"),
    (
        pytest.param(
            'examples/playbooks/blockincludes.yml',
            4, 2, id='block included tasks'),
        pytest.param(
            'examples/playbooks/blockincludes2.yml',
            4, 2, id='block included tasks with rescue and always',
        ),
        pytest.param(
            'examples/playbooks/taskincludes.yml',
            2, 1, id='included tasks'),
        pytest.param(
            'examples/playbooks/taskimports.yml',
            4, 2, id='import tasks 2 4 style'),
        pytest.param(
            'examples/playbooks/include-in-block.yml',
            3, 1, id='include tasks with block include',
        ),
        pytest.param(
            'examples/playbooks/include-import-tasks-in-role.yml',
            6, 3, id='include tasks in role',
        ),
    ),
)
def test_included_tasks(default_rules_collection, filename, file_count, match_count):
    """Check if number of loaded files is correct."""
    lintable = Lintable(filename)
    runner = Runner(default_rules_collection, lintable, [], [], [])
    result = runner.run()
    assert len(runner.playbooks) == file_count
    assert len(result) == match_count
