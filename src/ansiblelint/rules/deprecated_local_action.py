"""Implementation for deprecated-local-action rule."""
# Copyright (c) 2016, Tsukinowa Inc. <info@tsukinowa.jp>
# Copyright (c) 2018, Ansible Project
from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable


class TaskNoLocalAction(AnsibleLintRule):
    """Do not use 'local_action', use 'delegate_to: localhost'."""

    id = "deprecated-local-action"
    description = "Do not use ``local_action``, use ``delegate_to: localhost``"
    needs_raw_task = True
    severity = "MEDIUM"
    tags = ["deprecations"]
    version_added = "v4.0.0"

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> bool | str:
        """Return matches for a task."""
        raw_task = task["__raw_task__"]
        if "local_action" in raw_task.keys():
            return True

        return False


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    import pytest

    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.testing import RunFromText

    FAIL_TASK = """
    - name: Task example
      local_action:
        module: boto3_facts
    """

    SUCCESS_TASK = """
    - name: Task example
      boto3_facts:
      delegate_to: localhost # local_action
    """

    @pytest.mark.parametrize(("text", "expected"), ((SUCCESS_TASK, 0), (FAIL_TASK, 1)))
    def test_local_action(text: str, expected: int) -> None:
        """Positive test deprecated_local_action."""
        collection = RulesCollection()
        collection.register(TaskNoLocalAction())
        runner = RunFromText(collection)
        results = runner.run_role_tasks_main(text)
        assert len(results) == expected
