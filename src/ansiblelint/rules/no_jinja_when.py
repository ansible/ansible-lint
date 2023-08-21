"""Implementation of no-jinja-when rule."""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from ansiblelint.constants import LINE_NUMBER_KEY
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task


class NoFormattingInWhenRule(AnsibleLintRule):
    """No Jinja2 in when."""

    id = "no-jinja-when"
    description = (
        "``when`` is a raw Jinja2 expression, remove redundant {{ }} from variable(s)."
    )
    severity = "HIGH"
    tags = ["deprecations"]
    version_added = "historic"

    @staticmethod
    def _is_valid(when: str) -> bool:
        if isinstance(when, list):
            for item in when:
                if (
                    isinstance(item, str)
                    and item.find("{{") != -1
                    and item.find("}}") != -1
                ):
                    return False
            return True
        if not isinstance(when, str):
            return True
        return when.find("{{") == -1 and when.find("}}") == -1

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        errors: list[MatchError] = []
        if isinstance(data, dict):
            if "roles" not in data or data["roles"] is None:
                return errors
            errors = [
                self.create_matcherror(
                    details=str({"when": role}),
                    filename=file,
                    lineno=role[LINE_NUMBER_KEY],
                )
                for role in data["roles"]
                if (
                    isinstance(role, dict)
                    and "when" in role
                    and not self._is_valid(role["when"])
                )
            ]
        return errors

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> bool | str:
        return "when" in task.raw_task and not self._is_valid(task.raw_task["when"])


if "pytest" in sys.modules:
    # Tests for no-jinja-when rule.
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    def test_jinja_file_positive() -> None:
        """Positive test for no-jinja-when."""
        collection = RulesCollection()
        collection.register(NoFormattingInWhenRule())
        success = "examples/playbooks/rule-no-jinja-when-pass.yml"
        good_runner = Runner(success, rules=collection)
        assert [] == good_runner.run()

    def test_jinja_file_negative() -> None:
        """Negative test for no-jinja-when."""
        collection = RulesCollection()
        collection.register(NoFormattingInWhenRule())
        failure = "examples/playbooks/rule-no-jinja-when-fail.yml"
        bad_runner = Runner(failure, rules=collection)
        errs = bad_runner.run()
        assert len(errs) == 3
