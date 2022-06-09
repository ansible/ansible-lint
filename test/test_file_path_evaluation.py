"""Testing file path evaluation when using import_tasks / include_tasks."""
import textwrap
from pathlib import Path
from typing import Dict

import pytest

from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner

LAYOUT_IMPORTS: Dict[str, str] = {
    "main.yml": textwrap.dedent(
        """\
        ---
        - hosts: target
          gather_facts: false
          tasks:
            - name: from main import task 1
              ansible.builtin.import_tasks: tasks/task_1.yml
        """
    ),
    "tasks/task_1.yml": textwrap.dedent(
        """\
        ---
        - name: from task 1 import task 2
          ansible.builtin.import_tasks: tasks/task_2.yml
        """
    ),
    "tasks/task_2.yml": textwrap.dedent(
        """\
        ---
        - name: from task 2 import subtask 1
          ansible.builtin.import_tasks: tasks/subtasks/subtask_1.yml
        """
    ),
    "tasks/subtasks/subtask_1.yml": textwrap.dedent(
        """\
        ---
        - name: from subtask 1 import subtask 2
          import_tasks: tasks/subtasks/subtask_2.yml
        """
    ),
    "tasks/subtasks/subtask_2.yml": textwrap.dedent(
        """\
        ---
        - name: from subtask 2 do something
          debug:  # <-- expected to raise fqcn-builtins
            msg: |
              Something...
        """
    ),
}

LAYOUT_INCLUDES: Dict[str, str] = {
    "main.yml": textwrap.dedent(
        """\
        ---
        - hosts: target
          gather_facts: false
          tasks:
            - name: from main import task 1
              include_tasks: tasks/task_1.yml
        """
    ),
    "tasks/task_1.yml": textwrap.dedent(
        """\
        ---
        - name: from task 1 import task 2
          include_tasks: tasks/task_2.yml
        """
    ),
    "tasks/task_2.yml": textwrap.dedent(
        """\
        ---
        - name: from task 2 import subtask 1
          include_tasks: tasks/subtasks/subtask_1.yml
        """
    ),
    "tasks/subtasks/subtask_1.yml": textwrap.dedent(
        """\
        ---
        - name: from subtask 1 import subtask 2
          include_tasks: tasks/subtasks/subtask_2.yml
        """
    ),
    "tasks/subtasks/subtask_2.yml": textwrap.dedent(
        """\
        ---
        - name: from subtask 2 do something
          debug:  # <-- expected to raise fqcn-builtins
            msg: |
              Something...
        """
    ),
}


@pytest.mark.parametrize(
    "ansible_project_layout",
    (
        pytest.param(LAYOUT_IMPORTS, id="using only import_tasks"),
        pytest.param(LAYOUT_INCLUDES, id="using only include_tasks"),
    ),
)
def test_file_path_evaluation(
    tmp_path: Path,
    default_rules_collection: RulesCollection,
    ansible_project_layout: Dict[str, str],
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
    assert result[0].rule.id == "fqcn-builtins"
