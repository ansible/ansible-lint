"""Implementation of limiting number of tasks."""

from __future__ import annotations

import re
import sys
from typing import TYPE_CHECKING, Any

from ansiblelint.constants import LINE_NUMBER_KEY
from ansiblelint.rules import AnsibleLintRule, RulesCollection

if TYPE_CHECKING:
    from ansiblelint.config import Options
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

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        """Call matchplay for up to no_of_max_tasks inside file and return aggregate results."""
        results: list[MatchError] = []

        if file.kind != "playbook":
            return []
        tasks = data.get("tasks", [])
        if not isinstance(self._collection, RulesCollection):
            msg = "Rules cannot be run outside a rule collection."
            raise TypeError(msg)
        if len(tasks) > self._collection.options.max_tasks:
            results.append(
                self.create_matcherror(
                    message=f"Maximum tasks allowed in a play is {self._collection.options.max_tasks}.",
                    lineno=data[LINE_NUMBER_KEY],
                    tag=f"{self.id}[play]",
                    filename=file,
                ),
            )
        return results

    def matchtask(self, task: Task, file: Lintable | None = None) -> list[MatchError]:
        """Check if the task is a block and count the number of items inside it."""
        results: list[MatchError] = []

        if not isinstance(self._collection, RulesCollection):
            msg = "Rules cannot be run outside a rule collection."
            raise TypeError(msg)

        if task.action == "block/always/rescue":
            block_depth = self.calculate_block_depth(task)
            if block_depth > self._collection.options.max_block_depth:
                results.append(
                    self.create_matcherror(
                        message=f"Replace nested block with an include_tasks to make code easier to maintain. Maximum block depth allowed is {self._collection.options.max_block_depth}.",
                        lineno=task[LINE_NUMBER_KEY],
                        tag=f"{self.id}[nesting]",
                        filename=file,
                    ),
                )
        return results

    def calculate_block_depth(self, task: Task) -> int:
        """Recursively calculate the block depth of a task."""
        if not isinstance(task.position, str):
            raise NotImplementedError
        return task.position.count(".block")


if "pytest" in sys.modules:
    import pytest

    # pylint: disable=ungrouped-imports
    from ansiblelint.runner import Runner

    @pytest.mark.parametrize(
        ("file", "expected_results"),
        (
            pytest.param(
                "examples/playbooks/rule-complexity-pass.yml",
                [],
                id="pass",
            ),
            pytest.param(
                "examples/playbooks/rule-complexity-fail.yml",
                ["complexity[play]", "complexity[nesting]"],
                id="fail",
            ),
        ),
    )
    def test_complexity(
        file: str,
        expected_results: list[str],
        monkeypatch: pytest.MonkeyPatch,
        config_options: Options,
    ) -> None:
        """Test rule."""
        monkeypatch.setattr(config_options, "max_tasks", 5)
        monkeypatch.setattr(config_options, "max_block_depth", 3)
        collection = RulesCollection(options=config_options)
        collection.register(ComplexityRule())
        results = Runner(file, rules=collection).run()

        assert len(results) == len(expected_results)
        for i, result in enumerate(results):
            assert result.rule.id == ComplexityRule.id, result
            assert result.tag == expected_results[i]
