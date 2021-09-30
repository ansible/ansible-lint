from pathlib import Path

import pytest

from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner

IMPORTED_PLAYBOOK = '''\
- hosts: all
  tasks:
    - name: success
      fail: msg="fail"
      when: false
'''

MAIN_PLAYBOOK = '''\
- hosts: all

  tasks:
    - name: should be shell  # noqa command-instead-of-shell no-changed-when
      shell: echo lol

- import_playbook: imported_playbook.yml
'''


@pytest.fixture
def playbook(tmp_path: Path) -> str:
    """Create a reusable per-test playbook."""
    playbook_path = tmp_path / 'playbook.yml'
    playbook_path.write_text(MAIN_PLAYBOOK)
    (tmp_path / 'imported_playbook.yml').write_text(IMPORTED_PLAYBOOK)
    return str(playbook_path)


def test_skip_import_playbook(
    default_rules_collection: RulesCollection, playbook: str
) -> None:
    """Verify that a playbook import is skipped after a failure."""
    runner = Runner(playbook, rules=default_rules_collection)
    results = runner.run()
    assert len(results) == 0
