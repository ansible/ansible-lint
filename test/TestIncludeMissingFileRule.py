from collections import namedtuple

import pytest

from ansiblelint.runner import Runner

PlayFile = namedtuple('PlayFile', ['name', 'content'])


PLAY_INCLUDING_PLAIN = PlayFile('playbook.yml', u'''
- hosts: all
  tasks:
    - include: some_file.yml
''')

PLAY_INCLUDING_JINJA2 = PlayFile('playbook.yml', u'''
- hosts: all
  tasks:
    - include: "{{ some_path }}/some_file.yml"
''')

PLAY_INCLUDING_NOQA = PlayFile('playbook.yml', u'''
- hosts: all
  tasks:
    - include: some_file.yml # noqa 505
''')

PLAY_INCLUDED = PlayFile('some_file.yml', u'''
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
        p = tmp_path / play_file.name
        p.write_text(play_file.content)


@pytest.mark.parametrize(
    '_play_files', (pytest.param([PLAY_INCLUDING_PLAIN], id='referenced file missing'), ),
    indirect=['_play_files']
)
@pytest.mark.usefixtures('_play_files')
def test_include_file_missing(runner):
    results = str(runner.run())
    assert 'referenced missing file in' in results
    assert 'playbook.yml' in results
    assert 'some_file.yml' in results


@pytest.mark.parametrize(
    '_play_files',
    (
        pytest.param([PLAY_INCLUDING_PLAIN, PLAY_INCLUDED], id='File Exists'),
        pytest.param([PLAY_INCLUDING_JINJA2], id='JINJA2 in reference'),
        pytest.param([PLAY_INCLUDING_NOQA], id='NOQA was used')
    ),
    indirect=['_play_files']
)
@pytest.mark.usefixtures('_play_files')
def test_cases_that_do_not_report(runner):
    results = str(runner.run())
    assert 'referenced missing file in' not in results
