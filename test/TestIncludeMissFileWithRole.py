import os
from collections import namedtuple

import pytest

from ansiblelint.runner import Runner

PlayFile = namedtuple('PlayFile', ['name', 'content'])


PLAY_IN_THE_PLACE = PlayFile('playbook.yml', u'''
- hosts: all
  roles:
    - include_in_the_place
''')

PLAY_RELATIVE = PlayFile('playbook.yml', u'''
- hosts: all
  roles:
    - include_relative
''')

PLAY_MISS_INCLUDE = PlayFile('playbook.yml', u'''
- hosts: all
  roles:
    - include_miss
''')

PLAY_ROLE_INCLUDED_IN_THE_PLACE = PlayFile('roles/include_in_the_place/tasks/main.yml', u'''
---
- include_tasks: included_file.yml
''')

PLAY_ROLE_INCLUDED_RELATIVE = PlayFile('roles/include_relative/tasks/main.yml', u'''
---
- include_tasks: tasks/included_file.yml
''')

PLAY_ROLE_INCLUDED_MISS = PlayFile('roles/include_miss/tasks/main.yml', u'''
---
- include_tasks: tasks/noexist_file.yml
''')

PLAY_INCLUDED_IN_THE_PLACE = PlayFile('roles/include_in_the_place/tasks/included_file.yml', u'''
- debug:
    msg: 'was found & included'
''')

PLAY_INCLUDED_RELATIVE = PlayFile('roles/include_relative/tasks/included_file.yml', u'''
- debug:
    msg: 'was found & included'
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
        print(play_file.name)
        p = tmp_path / play_file.name
        os.makedirs(os.path.dirname(p), exist_ok=True)
        p.write_text(play_file.content)


@pytest.mark.parametrize(
    '_play_files',
    (
         pytest.param([PLAY_MISS_INCLUDE,
                       PLAY_ROLE_INCLUDED_MISS],
                      id='no exist file include'),
    ),
    indirect=['_play_files']
)
@pytest.mark.usefixtures('_play_files')
def test_cases_warning_message(runner, caplog):
    runner.run()
    noexist_message_count = 0

    for record in caplog.records:
        print(record)
        if "Couldn't open" in str(record):
            noexist_message_count += 1

    assert noexist_message_count == 1


@pytest.mark.parametrize(
    '_play_files',
    (
        pytest.param([PLAY_IN_THE_PLACE,
                      PLAY_ROLE_INCLUDED_IN_THE_PLACE,
                      PLAY_INCLUDED_IN_THE_PLACE],
                     id='in the place include'),
        pytest.param([PLAY_RELATIVE,
                      PLAY_ROLE_INCLUDED_RELATIVE,
                      PLAY_INCLUDED_RELATIVE],
                     id='relative include')
    ),
    indirect=['_play_files']
)
@pytest.mark.usefixtures('_play_files')
def test_cases_that_do_not_report(runner, caplog):
    runner.run()
    noexist_message_count = 0

    for record in caplog.records:
        if "Couldn't open" in str(record):
            noexist_message_count += 1

    assert noexist_message_count == 0
