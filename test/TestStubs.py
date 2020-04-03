from collections import namedtuple

import pytest

from ansiblelint import Runner


PlayFile = namedtuple('PlayFile', ['name', 'content'])


PLAY_STUBS = PlayFile('playbook.yml', '''
- hosts: localhost
  tasks:

    - name: include missing module white-listed via .ansible-lint
      a_missing_module:
        foo: bar
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
        pytest.param([PLAY_STUBS], id='Using stubs for missing modules'),
    ),
    indirect=['_play_files']
)
@pytest.mark.usefixtures('_play_files')
def test_stubs(runner):
    results = str(runner.run())
    assert not results
