"""Test related to skipping import_playbook."""

from pathlib import Path

from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner

IMPORTED_PLAYBOOK = """\
---
- name: Fixture
  hosts: all
  tasks:
    - name: Success # noqa: no-free-form
      ansible.builtin.fail: msg="fail"
      when: false
"""

MAIN_PLAYBOOK = """\
---
- name: Fixture
  hosts: all

  tasks:
    - name: Should be shell  # noqa: command-instead-of-shell no-changed-when no-free-form
      ansible.builtin.shell: echo lol

- name: Should not be imported
  import_playbook: imported_playbook.yml
"""


def test_skip_import_playbook(
    default_rules_collection: RulesCollection, tmp_path: Path
) -> None:
    """Verify that a playbook import is skipped after a failure."""
    playbook_path = tmp_path / "playbook.yml"
    playbook_path.write_text(MAIN_PLAYBOOK)
    (tmp_path / "imported_playbook.yml").write_text(IMPORTED_PLAYBOOK)

    runner = Runner(playbook_path, rules=default_rules_collection)
    results = runner.run()
    assert len(results) == 0
