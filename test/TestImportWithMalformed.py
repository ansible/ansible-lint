import pytest

from ansiblelint.file_utils import Lintable
from ansiblelint.runner import Runner

IMPORT_TASKS_MAIN = Lintable(
    'import-tasks-main.yml',
    '''\
- oops this is invalid
''',
)

IMPORT_SHELL_PIP = Lintable(
    'import-tasks-main.yml',
    '''\
- shell: pip
  changed: false
''',
)

PLAY_IMPORT_TASKS = Lintable(
    'playbook.yml',
    '''\
- hosts: all
  tasks:
    - import_tasks: import-tasks-main.yml
''',
)


@pytest.mark.parametrize(
    '_play_files',
    (
        pytest.param([IMPORT_SHELL_PIP, PLAY_IMPORT_TASKS], id='Import shell w/ pip'),
        pytest.param(
            [IMPORT_TASKS_MAIN, PLAY_IMPORT_TASKS],
            id='import_tasks w/ malformed import',
        ),
    ),
    indirect=['_play_files'],
)
@pytest.mark.usefixtures('_play_files')
def test_import_tasks_with_malformed_import(runner: Runner) -> None:
    """Test that malformed tasks/imports don't fail parsing."""
    results = runner.run()
    passed = False
    for result in results:
        if result.rule.id == 'syntax-check':
            passed = True
    assert passed, results
