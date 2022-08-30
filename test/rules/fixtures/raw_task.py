"""Test Rule that needs_raw_task."""
from __future__ import annotations

from typing import Any

from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule


class RawTaskRule(AnsibleLintRule):
    """Test rule that inspects the raw task."""

    id = "raw-task"
    shortdesc = "Test rule that inspects the raw task"
    tags = ["fake", "dummy", "test3"]
    needs_raw_task = True

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> bool | str:
        """Match a task using __raw_task__ to inspect the module params type."""
        raw_task = task["__raw_task__"]
        module = task["action"]["__ansible_module_original__"]
        found_raw_task_params = not isinstance(raw_task[module], dict)
        return found_raw_task_params
