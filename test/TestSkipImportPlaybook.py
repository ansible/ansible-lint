import pytest

from ansiblelint.runner import Runner

IMPORTED_PLAYBOOK = '''
- hosts: all
  tasks:
    - name: success
      fail: msg="fail"
      when: False
'''

MAIN_PLAYBOOK = '''
- hosts: all

  tasks:
    - name: should be shell  # noqa 305 301
      shell: echo lol

- import_playbook: imported_playbook.yml
'''


@pytest.fixture
def playbook(tmp_path):
    playbook_path = tmp_path / 'playbook.yml'
    playbook_path.write_text(MAIN_PLAYBOOK)
    (tmp_path / 'imported_playbook.yml').write_text(IMPORTED_PLAYBOOK)
    return str(playbook_path)


def test_skip_import_playbook(default_rules_collection, playbook):
    runner = Runner(default_rules_collection, playbook, [], [], [])
    results = runner.run()
    assert len(results) == 0
