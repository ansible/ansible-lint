from collections import namedtuple

import pytest

from ansiblelint.runner import Runner

PlayFile = namedtuple('PlayFile', ['name', 'content'])


IMPORT_TASKS_MAIN = PlayFile('import-tasks-main.yml', '''
- oops this is invalid
''')

IMPORT_SHELL_PIP = PlayFile('import-tasks-main.yml', '''
- shell: pip
''')

PLAY_IMPORT_TASKS = PlayFile('playbook.yml', '''
- hosts: all
  tasks:
    - import_tasks: import-tasks-main.yml
''')


@pytest.fixture
def play_file_path(tmp_path):
    p = tmp_path / 'playbook.yml'
    return str(p)


@pytest.fixture
def runner(play_file_path, default_rules_collection):
    return Runner(default_rules_collection, play_file_path, [], [], [])


@pytest.fixture
def _play_files(tmp_path, request):
    if request.param is None:
        return
    for play_file in request.param:
        p = tmp_path / play_file.name
        p.write_text(play_file.content)


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
                'https://github.com/ansible/ansible-lint/issues/707',
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
