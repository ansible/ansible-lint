import pytest
from _pytest.logging import LogCaptureFixture

from ansiblelint.file_utils import Lintable
from ansiblelint.runner import Runner

PLAY_IN_THE_PLACE = Lintable(
    'playbook.yml',
    '''\
- hosts: all
  roles:
    - include_in_the_place
''',
)

PLAY_RELATIVE = Lintable(
    'playbook.yml',
    '''\
- hosts: all
  roles:
    - include_relative
''',
)

PLAY_MISS_INCLUDE = Lintable(
    'playbook.yml',
    '''\
- hosts: all
  roles:
    - include_miss
''',
)

PLAY_ROLE_INCLUDED_IN_THE_PLACE = Lintable(
    'roles/include_in_the_place/tasks/main.yml',
    '''\
---
- include_tasks: included_file.yml
''',
)

PLAY_ROLE_INCLUDED_RELATIVE = Lintable(
    'roles/include_relative/tasks/main.yml',
    '''\
---
- include_tasks: tasks/included_file.yml
''',
)

PLAY_ROLE_INCLUDED_MISS = Lintable(
    'roles/include_miss/tasks/main.yml',
    '''\
---
- include_tasks: tasks/noexist_file.yml
''',
    kind="tasks",
)

PLAY_INCLUDED_IN_THE_PLACE = Lintable(
    'roles/include_in_the_place/tasks/included_file.yml',
    '''\
- debug:
    msg: 'was found & included'
''',
    kind="tasks",
)

PLAY_INCLUDED_RELATIVE = Lintable(
    'roles/include_relative/tasks/included_file.yml',
    '''\
- debug:
    msg: 'was found & included'
''',
)


@pytest.mark.parametrize(
    '_play_files',
    (
        pytest.param(
            [PLAY_MISS_INCLUDE, PLAY_ROLE_INCLUDED_MISS], id='no exist file include'
        ),
    ),
    indirect=['_play_files'],
)
@pytest.mark.usefixtures('_play_files')
def test_cases_warning_message(runner: Runner, caplog: LogCaptureFixture) -> None:
    """Test that including a non-existing file produces an error."""
    result = runner.run()

    assert len(result) == 1
    assert "No such file or directory" in result[0].message


@pytest.mark.parametrize(
    '_play_files',
    (
        pytest.param(
            [
                PLAY_IN_THE_PLACE,
                PLAY_ROLE_INCLUDED_IN_THE_PLACE,
                PLAY_INCLUDED_IN_THE_PLACE,
            ],
            id='in the place include',
        ),
        pytest.param(
            [PLAY_RELATIVE, PLAY_ROLE_INCLUDED_RELATIVE, PLAY_INCLUDED_RELATIVE],
            id='relative include',
        ),
    ),
    indirect=['_play_files'],
)
@pytest.mark.usefixtures('_play_files')
def test_cases_that_do_not_report(runner: Runner, caplog: LogCaptureFixture) -> None:
    """Test that relative inclusions are properly followed."""
    runner.run()
    noexist_message_count = 0

    for record in caplog.records:
        if "Couldn't open" in str(record):
            noexist_message_count += 1

    assert noexist_message_count == 0
