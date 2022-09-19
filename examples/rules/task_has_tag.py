"""Example implementation of a rule requiring tasks to have tags set."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable


class TaskHasTag(AnsibleLintRule):
    """Tasks must have tag."""

    id = "EXAMPLE001"
    description = "Tasks must have tag"
    tags = ["productivity", "tags"]

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> bool | str:
        """Task matching method."""
        if isinstance(task, str):
            return False

        # If the task include another task or make the playbook fail
        # Don't force to have a tag
        if not set(task.keys()).isdisjoint(["include", "fail"]):
            return False

        if not set(task.keys()).isdisjoint(["include_tasks", "fail"]):
            return False

        if not set(task.keys()).isdisjoint(["import_tasks", "fail"]):
            return False

        # Task should have tags
        if "tags" not in task:
            return True

        return False
