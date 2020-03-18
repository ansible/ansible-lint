from collections import namedtuple
import os

import pytest

from ansiblelint import Runner, RulesCollection


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
def rules():
    rulesdir = os.path.join('lib', 'ansiblelint', 'rules')
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
    'play_files', [pytest.param([PLAY_INCLUDING_PLAIN], id='referenced file missing')],
    indirect=['play_files']
)
def test_include_file_missing(runner, play_files):
    results = str(runner.run())
    assert 'referenced missing file in' in results
    assert 'playbook.yml' in results
    assert 'some_file.yml' in results


@pytest.mark.parametrize(
    'play_files',
    [
        pytest.param([PLAY_INCLUDING_PLAIN, PLAY_INCLUDED], id='File Exists'),
        pytest.param([PLAY_INCLUDING_JINJA2], id='JINJA2 in reference'),
        pytest.param([PLAY_INCLUDING_NOQA], id='NOQA was used')
    ],
    indirect=['play_files']
)
def test_cases_that_do_not_report(runner, play_files):
    results = str(runner.run())
    assert 'referenced missing file in' not in results
