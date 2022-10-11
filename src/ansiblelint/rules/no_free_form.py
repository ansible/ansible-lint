"""Implementation of NoFreeFormRule."""
from __future__ import annotations

import re
import sys
from typing import TYPE_CHECKING, Any

from ansiblelint._internal.rules import WarningRule
from ansiblelint.constants import INCLUSION_ACTION_NAMES, LINE_NUMBER_KEY
from ansiblelint.errors import MatchError
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable


class NoFreeFormRule(AnsibleLintRule):
    """Rule for detecting discouraged free-form syntax for action modules."""

    id = "no-free-form"
    description = "Avoid free-form inside files as it can produce subtile bugs."
    severity = "MEDIUM"
    tags = ["syntax", "risk", "experimental"]
    version_added = "v6.8.0"
    needs_raw_task = True
    cmd_shell_re = re.compile(
        r"(chdir|creates|executable|removes|stdin|stdin_add_newline|warn)="
    )

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> list[MatchError]:
        results: list[MatchError] = []
        action = task["action"]["__ansible_module_original__"]

        if action in INCLUSION_ACTION_NAMES:
            return results

        action_value = task["__raw_task__"].get(action, None)
        if task["action"].get("__ansible_module__", None) == "raw":
            if isinstance(action_value, str):
                if "executable=" in action_value:
                    results.append(
                        self.create_matcherror(
                            message="Avoid embedding `executable=` inside raw calls, use explicit args dictionary instead.",
                            linenumber=task[LINE_NUMBER_KEY],
                            filename=file,
                            tag=f"{self.id}[raw]",
                        )
                    )
            else:
                results.append(
                    MatchError(
                        message="Passing a non string value to `raw` module is neither document nor supported.",
                        linenumber=task[LINE_NUMBER_KEY],
                        filename=file,
                        tag="warning[raw-non-string]",
                        rule=WarningRule(),
                    )
                )
        elif isinstance(action_value, str) and "=" in action_value:
            fail = False
            if task["action"].get("__ansible_module__") in (
                "ansible.builtin.command",
                "ansible.builtin.shell",
                "ansible.windows.win_command",
                "ansible.windows.win_shell",
                "command",
                "shell",
                "win_command",
                "win_shell",
            ):
                if self.cmd_shell_re.match(action_value):
                    fail = True
            else:
                fail = True
            if fail:
                results.append(
                    self.create_matcherror(
                        message=f"Avoid using free-form when calling module actions. ({action})",
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
            pytest.param("examples/playbooks/rule-no-free-form-pass.yml", 0, id="pass"),
            pytest.param("examples/playbooks/rule-no-free-form-fail.yml", 2, id="fail"),
        ),
    )
    def test_rule_no_free_form(
        default_rules_collection: RulesCollection, file: str, expected: int
    ) -> None:
        """Validate that rule works as intended."""
        results = Runner(file, rules=default_rules_collection).run()

        for result in results:
            assert result.rule.id == NoFreeFormRule.id, result
        assert len(results) == expected
