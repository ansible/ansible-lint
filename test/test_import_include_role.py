"""Tests related to role imports."""
from __future__ import annotations

from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest

from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner

ROLE_TASKS_MAIN = """\
---
- name: Shell instead of command
  shell: echo hello world # noqa fqcn no-free-form
  changed_when: false
"""

ROLE_TASKS_WORLD = """\
---
- ansible.builtin.debug:
    msg: "this is a task without a name"
"""

PLAY_IMPORT_ROLE = """\
---
- name: Test fixture
  hosts: all

  tasks:
    - name: Some import # noqa: fqcn
      import_role:
        name: test-role
"""

PLAY_IMPORT_ROLE_FQCN = """\
---
- name: Test fixture
  hosts: all

  tasks:
    - name: Some import
      ansible.builtin.import_role:
        name: test-role
"""

PLAY_IMPORT_ROLE_INLINE = """\
---
- name: Fixture
  hosts: all
  tasks:
    - name: Some import
      import_role: name=test-role  # noqa: no-free-form fqcn
"""

PLAY_INCLUDE_ROLE = """\
---
- name: Fixture
  hosts: all
  tasks:
    - name: Some import
      include_role:
        name: test-role
        tasks_from: world
"""

PLAY_INCLUDE_ROLE_FQCN = """\
---
- name: Fixture
  hosts: all
  tasks:
    - name: Some import
      ansible.builtin.include_role:
        name: test-role
        tasks_from: world
"""

PLAY_INCLUDE_ROLE_INLINE = """\
---
- name: Fixture
  hosts: all
  tasks:
    - name: Some import
      include_role: name=test-role tasks_from=world  # noqa: no-free-form
"""


@pytest.fixture(name="playbook_path")
def fixture_playbook_path(request: SubRequest, tmp_path: Path) -> str:
    """Create a reusable per-test role skeleton."""
    playbook_text = request.param
    role_tasks_dir = tmp_path / "test-role" / "tasks"
    role_tasks_dir.mkdir(parents=True)
    (role_tasks_dir / "main.yml").write_text(ROLE_TASKS_MAIN)
    (role_tasks_dir / "world.yml").write_text(ROLE_TASKS_WORLD)
    play_path = tmp_path / "playbook.yml"
    play_path.write_text(playbook_text)
    return str(play_path)


@pytest.mark.parametrize(
    ("playbook_path", "messages"),
    (
        pytest.param(
            PLAY_IMPORT_ROLE,
            ["only when shell functionality is required", "All tasks should be named"],
            id="IMPORT_ROLE",
        ),
        pytest.param(
            PLAY_IMPORT_ROLE_FQCN,
            ["only when shell functionality is required", "All tasks should be named"],
            id="IMPORT_ROLE_FQCN",
        ),
        pytest.param(
            PLAY_IMPORT_ROLE_INLINE,
            ["only when shell functionality is require", "All tasks should be named"],
            id="IMPORT_ROLE_INLINE",
        ),
        pytest.param(
            PLAY_INCLUDE_ROLE,
            ["only when shell functionality is require", "All tasks should be named"],
            id="INCLUDE_ROLE",
        ),
        pytest.param(
            PLAY_INCLUDE_ROLE_FQCN,
            ["only when shell functionality is require", "All tasks should be named"],
            id="INCLUDE_ROLE_FQCN",
        ),
        pytest.param(
            PLAY_INCLUDE_ROLE_INLINE,
            ["only when shell functionality is require", "All tasks should be named"],
            id="INCLUDE_ROLE_INLINE",
        ),
    ),
    indirect=("playbook_path",),
)
def test_import_role2(
    default_rules_collection: RulesCollection, playbook_path: str, messages: list[str]
) -> None:
    """Test that include_role digs deeper than import_role."""
    runner = Runner(
        playbook_path,
        rules=default_rules_collection,
        skip_list=["fqcn[action-core]"],
    )
    results = runner.run()
    for message in messages:
        assert message in str(results)
    # Ensure no other unexpected messages are present
    assert len(messages) == len(results), results
