import pytest

from ansiblelint.file_utils import Lintable

IMPORT_TASKS_MAIN = Lintable('import-tasks-main.yml', '''
- oops this is invalid
''')

IMPORT_SHELL_PIP = Lintable('import-tasks-main.yml', '''
- shell: pip
''')

PLAY_IMPORT_TASKS = Lintable('playbook.yml', '''
- hosts: all
  tasks:
    - import_tasks: import-tasks-main.yml
''')


@pytest.mark.parametrize(
    '_play_files',
    (
        pytest.param([IMPORT_SHELL_PIP, PLAY_IMPORT_TASKS], id='Import shell w/ pip'),
        pytest.param(
            [IMPORT_TASKS_MAIN, PLAY_IMPORT_TASKS],
            id='import_tasks w/ malformed import',
            marks=pytest.mark.xfail(
                reason='Garbage non-tasks sequence is not being '
                'properly processed. Ref: '
                'https://github.com/ansible-community/ansible-lint/issues/707',
                raises=AttributeError,
            ),
        ),
    ),
    indirect=['_play_files']
)
@pytest.mark.usefixtures('_play_files')
def test_import_tasks_with_malformed_import(runner):
    results = str(runner.run())
    assert 'only when shell functionality is required' in results
