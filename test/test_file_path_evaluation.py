"""Testing file path evaluation when using import_tasks / include_tasks."""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

import pytest

from ansiblelint.runner import Runner

if TYPE_CHECKING:
    from pathlib import Path

    from ansiblelint.rules import RulesCollection

LAYOUT_IMPORTS: dict[str, str] = {
    "main.yml": textwrap.dedent(
        """\
        ---
        - name: Fixture
          hosts: target
          gather_facts: false
          tasks:
            - name: From main import task 1
              ansible.builtin.import_tasks: tasks/task_1.yml
        """,
    ),
    "tasks/task_1.yml": textwrap.dedent(
        """\
        ---
        - name: task_1 | From task 1 import task 2
          ansible.builtin.import_tasks: tasks/task_2.yml
        """,
    ),
    "tasks/task_2.yml": textwrap.dedent(
        """\
        ---
        - name: task_2 | From task 2 import subtask 1
          ansible.builtin.import_tasks: tasks/subtasks/subtask_1.yml
        """,
    ),
    "tasks/subtasks/subtask_1.yml": textwrap.dedent(
        """\
        ---
        - name: subtasks | subtask_1 | From subtask 1 import subtask 2
          ansible.builtin.import_tasks: tasks/subtasks/subtask_2.yml
        """,
    ),
    "tasks/subtasks/subtask_2.yml": textwrap.dedent(
        """\
        ---
        - name: subtasks | subtask_2 | From subtask 2 do something
          debug:  # <-- expected to raise fqcn[action-core]
            msg: |
              Something...
        """,
    ),
}

LAYOUT_INCLUDES: dict[str, str] = {
    "main.yml": textwrap.dedent(
        """\
        ---
        - name: Fixture
          hosts: target
          gather_facts: false
          tasks:
            - name: From main import task 1
              ansible.builtin.include_tasks: tasks/task_1.yml
        """,
    ),
    "tasks/task_1.yml": textwrap.dedent(
        """\
        ---
        - name: task_1 | From task 1 import task 2
          ansible.builtin.include_tasks: tasks/task_2.yml
        """,
    ),
    "tasks/task_2.yml": textwrap.dedent(
        """\
        ---
        - name: task_2 | From task 2 import subtask 1
          ansible.builtin.include_tasks: tasks/subtasks/subtask_1.yml
        """,
    ),
    "tasks/subtasks/subtask_1.yml": textwrap.dedent(
        """\
        ---
        - name: subtasks | subtask_1 | From subtask 1 import subtask 2
          ansible.builtin.include_tasks: tasks/subtasks/subtask_2.yml
        """,
    ),
    "tasks/subtasks/subtask_2.yml": textwrap.dedent(
        """\
        ---
        - name: subtasks | subtask_2 | From subtask 2 do something
          debug:  # <-- expected to raise fqcn[action-core]
            msg: |
              Something...
        """,
    ),
}


@pytest.mark.parametrize(
    "ansible_project_layout",
    (
        pytest.param(LAYOUT_IMPORTS, id="using-only-import_tasks"),
        pytest.param(LAYOUT_INCLUDES, id="using-only-include_tasks"),
    ),
)
def test_file_path_evaluation(
    tmp_path: Path,
    default_rules_collection: RulesCollection,
    ansible_project_layout: dict[str, str],
) -> None:
    """Test file path evaluation when using import_tasks / include_tasks in the project.

    The goal of this test is to verify our ability to find errors from within
    nested includes.
    """
    for file_path, file_content in ansible_project_layout.items():
        full_path = tmp_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(file_content)

    result = Runner(str(tmp_path), rules=default_rules_collection).run()

    assert len(result) == 1
    assert result[0].rule.id == "fqcn"


def test_include_tasks_file_path_uses_parent_playbook_context(
    tmp_path: Path,
    default_rules_collection: RulesCollection,
) -> None:
    """Check include_tasks file paths in nested tasks can use playbook context."""
    ansible_project_layout = {
        "extensions/molecule/shared/playbooks/prepare.yml": textwrap.dedent(
            """\
            ---
            - name: Fixture
              hosts: localhost
              gather_facts: false
              tasks:
                - name: Include scenario prepare tasks
                  ansible.builtin.include_tasks: ../../default/tasks/prepare/all.yml
            """,
        ),
        "extensions/molecule/default/tasks/prepare/all.yml": textwrap.dedent(
            """\
            ---
            - name: Init state via shared task
              ansible.builtin.include_tasks:
                file: ../tasks/state_update.yml
            """,
        ),
        "extensions/molecule/shared/tasks/state_update.yml": textwrap.dedent(
            """\
            ---
            - name: Merge update into state
              ansible.builtin.debug:
                msg: State updated
            """,
        ),
    }
    for file_path, file_content in ansible_project_layout.items():
        full_path = tmp_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(file_content)

    runner = Runner(
        str(tmp_path / "extensions/molecule/shared/playbooks/prepare.yml"),
        rules=default_rules_collection,
    )
    result = runner.run()

    assert not [match for match in result if match.rule.id == "load-failure"]
    assert any(
        lintable.path.name == "state_update.yml" for lintable in runner.lintables
    )
