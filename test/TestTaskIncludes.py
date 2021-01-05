import pytest

from ansiblelint.file_utils import Lintable
from ansiblelint.runner import Runner


@pytest.mark.parametrize(
    ('filename', 'file_count', "match_count"),
    (
        pytest.param(
            'examples/playbooks/blockincludes.yml',
            4, 2, id='blockincludes'),
        pytest.param(
            'examples/playbooks/blockincludes2.yml',
            4, 2, id='blockincludes2',
        ),
        pytest.param(
            'examples/playbooks/taskincludes.yml',
            2, 1, id='taskincludes'),
        pytest.param(
            'examples/playbooks/taskimports.yml',
            4, 2, id='taskimports'),
        pytest.param(
            'examples/playbooks/include-in-block.yml',
            3, 1, id='include-in-block',
        ),
        pytest.param(
            'examples/playbooks/include-import-tasks-in-role.yml',
            5, 2, id='role_with_task_inclusions',
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
