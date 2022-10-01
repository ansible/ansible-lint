"""Implementation of NoShorthandRule."""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from ansiblelint.constants import INCLUSION_ACTION_NAMES, LINE_NUMBER_KEY
from ansiblelint.errors import MatchError
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable


class NoShorthandRule(AnsibleLintRule):
    """Rule for detecting discouraged shorthand syntax for action modules."""

    id = "no-shorthand"
    description = "Avoid shorthand inside files as it can produce subtile bugs."
    severity = "MEDIUM"
    tags = ["syntax", "risk", "experimental"]
    version_added = "v6.8.0"
    needs_raw_task = True

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> list[MatchError]:
        results: list[MatchError] = []
        action = task["action"]["__ansible_module_original__"]

        if action in INCLUSION_ACTION_NAMES:
            return results

        action_value = task["__raw_task__"].get(action, None)
        if isinstance(action_value, str) and "=" in action_value:
            results.append(
                self.create_matcherror(
                    message=f"Avoid using shorthand (free-form) when calling module actions. ({action})",
                    linenumber=task[LINE_NUMBER_KEY],
                    filename=file,
                )
            )
        return results


if "pytest" in sys.modules:  # noqa: C901

    import pytest

    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.runner import Runner  # pylint: disable=ungrouped-imports

    @pytest.mark.parametrize(
        ("file", "expected"),
        (
            pytest.param("examples/playbooks/rule-no-shorthand-pass.yml", 0, id="pass"),
            pytest.param("examples/playbooks/rule-no-shorthand-fail.yml", 1, id="fail"),
        ),
    )
    def test_rule_no_shorthand(
        default_rules_collection: RulesCollection, file: str, expected: int
    ) -> None:
        """Validate that rule works as intended."""
        results = Runner(file, rules=default_rules_collection).run()

        for result in results:
            assert result.rule.id == NoShorthandRule.id, result
        assert len(results) == expected
