"""Tests related to use of noqa inside playbooks."""
import pytest

from ansiblelint.testing import RunFromText

PLAYBOOK_PRE_TASKS = """\
---
- name: Fixture
  hosts: all
  tasks:
    - name: Bad git 1  # noqa latest[git]
      action: ansible.builtin.git a=b c=d
    - name: Bad git 2
      action: ansible.builtin.git a=b c=d
  pre_tasks:
    - name: Bad git 3  # noqa latest[git]
      action: ansible.builtin.git a=b c=d
    - name: Bad git 4
      action: ansible.builtin.git a=b c=d
"""

PLAYBOOK_POST_TASKS = """\
---
- name: Fixture
  hosts: all
  tasks:
    - name: Bad git 1  # noqa latest[git]
      action: ansible.builtin.git a=b c=d
    - name: Bad git 2
      action: ansible.builtin.git a=b c=d
  post_tasks:
    - name: Bad git 3  # noqa latest[git]
      action: ansible.builtin.git a=b c=d
    - name: Bad git 4
      action: ansible.builtin.git a=b c=d
"""

PLAYBOOK_HANDLERS = """\
---
- name: Fixture
  hosts: all
  tasks:
    - name: Bad git 1  # noqa latest[git]
      action: ansible.builtin.git a=b c=d
    - name: Bad git 2
      action: ansible.builtin.git a=b c=d
  handlers:
    - name: Bad git 3  # noqa latest[git]
      action: ansible.builtin.git a=b c=d
    - name: Bad git 4
      action: ansible.builtin.git a=b c=d
"""

PLAYBOOK_TWO_PLAYS = """\
---
- name: Fixture
  hosts: all
  tasks:
    - name: Bad git 1  # noqa latest[git]
      action: ansible.builtin.git a=b c=d
    - name: Bad git 2
      action: ansible.builtin.git a=b c=d

- name: Fixture 2
  hosts: all
  tasks:
    - name: Bad git 3  # noqa latest[git]
      action: ansible.builtin.git a=b c=d
    - name: Bad git 4
      action: ansible.builtin.git a=b c=d
"""

PLAYBOOK_WITH_BLOCK = """\
---
- name: Fixture
  hosts: all
  tasks:
    - name: Bad git 1  # noqa latest[git]
      action: ansible.builtin.git a=b c=d
    - name: Bad git 2
      action: ansible.builtin.git a=b c=d
    - name: Block with rescue and always section
      block:
        - name: Bad git 3  # noqa latest[git]
          action: ansible.builtin.git a=b c=d
        - name: Bad git 4
          action: ansible.builtin.git a=b c=d
      rescue:
        - name: Bad git 5  # noqa latest[git]
          action: ansible.builtin.git a=b c=d
        - name: Bad git 6
          action: ansible.builtin.git a=b c=d
      always:
        - name: Bad git 7  # noqa latest[git]
          action: ansible.builtin.git a=b c=d
        - name: Bad git 8
          action: ansible.builtin.git a=b c=d
"""


@pytest.mark.parametrize(
    ("playbook", "length"),
    (
        pytest.param(PLAYBOOK_PRE_TASKS, 2, id="PRE_TASKS"),
        pytest.param(PLAYBOOK_POST_TASKS, 2, id="POST_TASKS"),
        pytest.param(PLAYBOOK_HANDLERS, 2, id="HANDLERS"),
        pytest.param(PLAYBOOK_TWO_PLAYS, 2, id="TWO_PLAYS"),
        pytest.param(PLAYBOOK_WITH_BLOCK, 4, id="WITH_BLOCK"),
    ),
)
def test_pre_tasks(
    default_text_runner: RunFromText, playbook: str, length: int
) -> None:
    """Check that skipping is possible in different playbook parts."""
    # When
    results = default_text_runner.run_playbook(playbook)

    # Then
    assert len(results) == length
