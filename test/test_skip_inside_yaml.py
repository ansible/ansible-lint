"""Tests related to use of inline noqa."""
import pytest

from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner
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
    ("lintable", "expected"),
    (pytest.param("examples/playbooks/test_skip_inside_yaml.yml", 7, id="yaml"),),
)
def test_inline_skips(
    default_rules_collection: RulesCollection, lintable: str, expected: int
) -> None:
    """Check that playbooks can contain skips."""
    results = Runner(lintable, rules=default_rules_collection).run()

    assert len(results) == expected


def test_role_meta() -> None:
    """Test running from inside meta folder."""
    role_path = "examples/roles/meta_noqa"

    result = run_ansible_lint("-v", role_path)
    assert len(result.stdout) == 0
    assert result.returncode == 0
