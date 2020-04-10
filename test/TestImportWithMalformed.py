from collections import namedtuple
from pathlib import Path

import pytest

from ansiblelint import Runner, RulesCollection


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
def rules():
    rulesdir = str(Path('lib') / 'ansiblelint' / 'rules')
    return RulesCollection([rulesdir])


@pytest.fixture
def runner(play_file_path, rules):
    return Runner(rules, play_file_path, [], [], [])


@pytest.fixture
def play_files(tmp_path, request):
    if request.param is None:
        return
    for play_file in request.param:
        p = tmp_path / play_file.name
        p.write_text(play_file.content)


@pytest.mark.parametrize(
    'play_files',
    [
        pytest.param([IMPORT_SHELL_PIP, PLAY_IMPORT_TASKS], id='Import shell w/ pip'),
        pytest.param([IMPORT_TASKS_MAIN, PLAY_IMPORT_TASKS], id='import_tasks w/ malformed import')
    ],
    indirect=['play_files']
)
def test_import_tasks_with_malformed_import(runner, play_files):
    results = str(runner.run())
    assert 'only when shell functionality is required' in results
