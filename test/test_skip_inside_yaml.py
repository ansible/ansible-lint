"""Tests related to use of inline noqa."""
import pytest

from ansiblelint.testing import RunFromText, run_ansible_lint

ROLE_TASKS = """\
---
- ansible.builtin.debug:
    msg: this should fail linting due lack of name
- ansible.builtin.debug:  # noqa unnamed-task
    msg: this should pass due to noqa comment
"""

ROLE_TASKS_WITH_BLOCK = """\
---
- name: Bad git 1  # noqa git-latest
  action: ansible.builtin.git a=b c=d
- name: Bad git 2
  action: ansible.builtin.git a=b c=d
- name: Block with rescue and always section
  block:
    - name: Bad git 3  # noqa git-latest
      action: ansible.builtin.git a=b c=d
    - name: Bad git 4
      action: ansible.builtin.git a=b c=d
  rescue:
    - name: Bad git 5  # noqa git-latest
      action: ansible.builtin.git a=b c=d
    - name: Bad git 6
      action: ansible.builtin.git a=b c=d
  always:
    - name: Bad git 7  # noqa git-latest
      action: ansible.builtin.git a=b c=d
    - name: Bad git 8
      action: ansible.builtin.git a=b c=d
"""

PLAYBOOK = """\
---
- name: Fixture
  hosts: all
  tasks:
    - name: Test hg-latest
      action: ansible.builtin.hg
    - name: Test hg-latest (skipped)  # noqa hg-latest
      action: ansible.builtin.hg

    - name: Test git-latest and partial-become
      become_user: alice
      action: ansible.builtin.git
    - name: Test git-latest and partial-become (skipped)  # noqa git-latest partial-become
      become_user: alice
      action: ansible.builtin.git

    - name: Test YAML and jinja[spacing]
      ansible.builtin.get_url:
        # noqa: risky-file-permissions
        url: http://example.com/really_long_path/really_long_path/really_long_path/really_long_path/really_long_path/really_long_path/really_long_path/really_long_path/file.conf
        dest: "{{dest_proj_path}}/foo.conf"
    - name: Test YAML and jinja[spacing] (skipped)
      ansible.builtin.get_url:
        # noqa: risky-file-permissions
        url: http://example.com/really_long_path/really_long_path/really_long_path/really_long_path/really_long_path/really_long_path/really_long_path/really_long_path/file.conf  # noqa yaml
        dest: "{{dest_proj_path}}/foo.conf"  # noqa jinja[spacing]

    - name: Test deprecated-command-syntax
      ansible.builtin.command: creates=B chmod 644 A
    - name: Test deprecated-command-syntax
      ansible.builtin.command: warn=yes creates=B chmod 644 A
    - name: Test deprecated-command-syntax (skipped via no warn)
      ansible.builtin.command: warn=no creates=B chmod 644 A
    - name: Test deprecated-command-syntax (skipped via skip_ansible_lint)
      ansible.builtin.command: creates=B chmod 644 A
      tags:
        - skip_ansible_lint
"""

ROLE_TASKS_WITH_BLOCK_BECOME = """\
---
- name: Fixture
  hosts: localhost
  tasks:
    - name: Foo
      become: true
      block:
        - name: Bar
          become_user: john_doe
          ansible.builtin.command: "/etc/test.sh"
          changed_when: false
"""


def test_role_tasks(default_text_runner: RunFromText) -> None:
    """Check that role tasks can contain skips."""
    results = default_text_runner.run_role_tasks_main(ROLE_TASKS)
    assert len(results) == 1, results
    assert results[0].linenumber == 2
    assert results[0].tag == "name[missing]"
    assert results[0].rule.id == "name"


def test_role_tasks_with_block(default_text_runner: RunFromText) -> None:
    """Check that blocks in role tasks can contain skips."""
    results = default_text_runner.run_role_tasks_main(ROLE_TASKS_WITH_BLOCK)
    assert len(results) == 4


@pytest.mark.parametrize(
    ("playbook_src", "results_num"),
    (
        (PLAYBOOK, 8),
        (ROLE_TASKS_WITH_BLOCK_BECOME, 0),
    ),
    ids=("generic", "with block become inheritance"),
)
def test_playbook(
    default_text_runner: RunFromText, playbook_src: str, results_num: int
) -> None:
    """Check that playbooks can contain skips."""
    results = default_text_runner.run_playbook(playbook_src)
    assert len(results) == results_num


def test_role_meta() -> None:
    """Test running from inside meta folder."""
    role_path = "examples/roles/meta_noqa"

    result = run_ansible_lint("-v", role_path)
    assert len(result.stdout) == 0
    assert result.returncode == 0
