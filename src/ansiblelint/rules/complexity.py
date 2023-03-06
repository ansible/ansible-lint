"""Implementation of maximum size for number of tasks within a block"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from collections.abc import Iterable
import ansiblelint

from ansiblelint.constants import LINE_NUMBER_KEY
from ansiblelint.errors import MatchError
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable  # noqa: F811


class CountTasksRule(AnsibleLintRule):
    """Rule for counting maximum number of tasks"""

    id = "complexity"
    description = (
        "All tasks and plays should have a distinct name for readability "
        "and for ``--start-at-task`` to work"
    )
    severity = "MEDIUM"
    tags = ["idiom"]
    version_added = "v6.9.1 (last update)"
    _re_templated_inside = re.compile(r".*\{\{.*\}\}.*\w.*$")

    def matchtasks(self, file: Lintable) -> Iterable[MatchError]:
        """Count the number of tasks inside a YAML file."""
        count = 0
        if (
            file.kind not in ["handlers", "tasks", "playbook"]
            or str(file.base_kind) != "text/yaml"
        ):
            return []

        tasks_iterator = ansiblelint.yaml_utils.iter_tasks_in_file(file)
        for task, skipped_tags in tasks_iterator:
            if (
                self.id in skipped_tags
                or ("action" not in task)
                or "skip_ansible_lint" in task.get("tags", [])
            ):
                continue

            count += 1

        return [
            MatchError(
                filename=file,
                linenumber=task[LINE_NUMBER_KEY],
                rule=self.id,
                message="The file contains {count} tasks",
            )
        ]
