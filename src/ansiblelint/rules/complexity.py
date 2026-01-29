"""Implementation of limiting number of tasks."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from ansiblelint.rules import AnsibleLintRule, RulesCollection

if TYPE_CHECKING:
    from ansiblelint.app import App
    from ansiblelint.config import Options
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task


class ComplexityRule(AnsibleLintRule):
    """Sets maximum complexity to avoid complex plays."""

    id = "complexity"
    description = "Checks for complex plays and tasks"
    link = "https://ansible.readthedocs.io/projects/lint/rules/complexity/"
    severity = "MEDIUM"
    tags = ["experimental"]

    def __init__(self) -> None:
        """Initialize the rule."""
        super().__init__()
        self._collection: RulesCollection | None = None

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        """Call matchplay for up to no_of_max_tasks inside file and return aggregate results."""
        results: list[MatchError] = []

        if file.kind != "playbook":
            return []
        tasks = data.get("tasks", [])
        if not isinstance(self._collection, RulesCollection):  # pragma: no cover
            msg = "Rules cannot be run outside a rule collection."
            raise TypeError(msg)
        if len(tasks) > self._collection.options.max_tasks:
            results.append(
                self.create_matcherror(
                    message=f"Maximum tasks allowed in a play is {self._collection.options.max_tasks}.",
                    tag=f"{self.id}[play]",
                    filename=file,
                    data=data,
                ),
            )
        return results

    def matchtask(self, task: Task, file: Lintable | None = None) -> list[MatchError]:
        """Check if the task is a block and count the number of items inside it."""
        results: list[MatchError] = []

        if not isinstance(self._collection, RulesCollection):  # pragma: no cover
            msg = "Rules cannot be run outside a rule collection."
            raise TypeError(msg)

        if task.action == "block/always/rescue":
            block_depth = self.calculate_block_depth(task)
            if block_depth > self._collection.options.max_block_depth:
                results.append(
                    self.create_matcherror(
                        message=f"Replace nested block with an include_tasks to make code easier to maintain. Maximum block depth allowed is {self._collection.options.max_block_depth}.",
                        lineno=task.line,
                        tag=f"{self.id}[nesting]",
                        filename=file,
                    ),
                )
        return results

    def matchtasks(self, file: Lintable) -> list[MatchError]:
        """Call matchtask for each task and check total task count."""
        matches: list[MatchError] = []

        if not isinstance(self._collection, RulesCollection):  # pragma: no cover
            msg = "Rules cannot be run outside a rule collection."
            raise TypeError(msg)

        # Call parent's matchtasks to get all individual task violations
        matches = super().matchtasks(file)

        # Only check total task count for task files and handler files
        # Playbooks use the complexity[play] check instead
        if file.kind in ["handlers", "tasks"]:
            # pylint: disable=import-outside-toplevel
            from ansiblelint.utils import task_in_list

            task_count = sum(
                1
                for _ in task_in_list(
                    data=file.data,
                    file=file,
                    kind=file.kind,
                )
            )

            # Check if total task count exceeds limit
            if task_count > self._collection.options.max_tasks:
                matches.append(
                    self.create_matcherror(
                        message=f"File contains {task_count} tasks, exceeding the maximum of {self._collection.options.max_tasks}. Consider using `ansible.builtin.include_tasks` to split the tasks into smaller files.",
                        tag=f"{self.id}[tasks]",
                        filename=file,
                    ),
                )

        return matches

    def calculate_block_depth(self, task: Task) -> int:
        """Recursively calculate the block depth of a task."""
        if not isinstance(task.position, str):  # pragma: no cover
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
            pytest.param(
                "examples/playbooks/tasks/rule-complexity-tasks-fail.yml",
                ["complexity[tasks]"],
                id="tasks",
            ),
        ),
    )
    def test_complexity(
        file: str,
        expected_results: list[str],
        monkeypatch: pytest.MonkeyPatch,
        config_options: Options,
        app: App,
    ) -> None:
        """Test rule."""
        monkeypatch.setattr(config_options, "max_tasks", 5)
        monkeypatch.setattr(config_options, "max_block_depth", 3)
        collection = RulesCollection(app=app, options=config_options)
        collection.register(ComplexityRule())
        results = Runner(file, rules=collection).run()

        assert len(results) == len(expected_results)
        for i, result in enumerate(results):
            assert result.rule.id == ComplexityRule.id, result
            assert result.tag == expected_results[i]
