"""Implementation of limiting number of tasks."""
from __future__ import annotations

import re
import sys
from typing import TYPE_CHECKING, Any

from ansiblelint.config import options
from ansiblelint.constants import LINE_NUMBER_KEY
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task


class ComplexityRule(AnsibleLintRule):
    """Rule for limiting number of tasks inside a file."""

    id = "complexity"
    description = "There should be limited tasks executed inside any file"
    severity = "MEDIUM"
    tags = ["experimental", "idiom"]
    version_added = "v6.18.0 (last update)"
    _re_templated_inside = re.compile(r".*\{\{.*\}\}.*\w.*$")
    max_tasks = options.max_tasks
    max_block_depth = options.max_block_depth

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        """Call matchplay for up to no_of_max_tasks inside file and return aggregate results."""
        results: list[MatchError] = []

        if file.kind != "playbook":
            return []
        tasks = data.get("tasks", [])
        if len(tasks) > options.max_tasks:
            results.append(
                self.create_matcherror(
                    message=f"Maximum tasks allowed in a play is {options.max_tasks}.",
                    lineno=data[LINE_NUMBER_KEY],
                    tag=f"{self.id}[play]",
                    filename=file,
                ),
            )
        return results

    def matchtask(self, task: Task, file: Lintable | None = None) -> list[MatchError]:
        """Check if the task is a block and count the number of items inside it."""
        results: list[MatchError] = []

        if task.__class__.__name__ == "block":
            block_depth = self.calculate_block_depth(task)
            if block_depth > self.max_block_depth:
                results.append(
                    self.create_matcherror(
                        message=f"Replace long block with an include_tasks to make code easier to maintain. Maximum block depth allowed in a play is {self.max_block_depth}.",
                        lineno=task[LINE_NUMBER_KEY],
                        tag=f"{self.id}[task]",
                        filename=file,
                    ),
                )
        return results

    def calculate_block_depth(self, task: Task, depth: int = 0) -> int:
        """Recursively calculate the block depth of a task."""
        block_depth = depth
        block_items = task.get("tasks", [])
        for block_task in block_items:
            if block_task.__class__.__name__ == "block":
                block_depth = max(
                    block_depth,
                    self.calculate_block_depth(block_task, depth + 1),
                )
        return block_depth


if "pytest" in sys.modules:
    import pytest

    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.runner import Runner  # pylint: disable=ungrouped-imports

    @pytest.mark.parametrize(
        ("file", "expected"),
        (
            pytest.param(
                "examples/playbooks/rule-complexity-pass.yml",
                0,
                id="pass",
            ),
            pytest.param(
                "examples/playbooks/rule-complexity-fail.yml",
                1,
                id="fail",
            ),
        ),
    )
    def test_complexity(
        default_rules_collection: RulesCollection,
        file: str,
        expected: int,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test rule."""
        monkeypatch.setattr(options, "max_tasks", 5)
        monkeypatch.setattr(options, "max_block_depth", 20)
        collection = RulesCollection()
        collection.register(ComplexityRule())
        results = Runner(file, rules=default_rules_collection).run()

        for result in results:
            assert result.rule.id == ComplexityRule.id, result
            assert result.tag == "complexity[play]"
        assert len(results) == expected
