"""Optional Ansible-lint rule to warn use of run_once with strategy free."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from ansiblelint.constants import LINE_NUMBER_KEY
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task


class RunOnce(AnsibleLintRule):
    """Run once should use strategy other than free."""

    id = "run-once"
    link = "https://docs.ansible.com/ansible/latest/reference_appendices/playbooks_keywords.html"
    description = "When using run_once, we should avoid using strategy as free."

    tags = ["idiom"]
    severity = "MEDIUM"
    _ids = {
        "run-once[task]": "Using run_once may behave differently if strategy is set to free.",
        "run-once[play]": "Play uses strategy: free",
    }

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        """Return matches found for a specific playbook."""
        # If the Play uses the 'strategy' and it's value is set to free

        if not file or file.kind != "playbook" or not data:
            return []

        strategy = data.get("strategy")
        run_once = data.get("run_once", False)
        if (not strategy and not run_once) or strategy != "free":
            return []
        return [
            self.create_matcherror(
                message="Play uses strategy: free",
                filename=file,
                tag=f"{self.id}[play]",
                lineno=strategy._line_number,  # noqa: SLF001
            ),
        ]

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> list[MatchError]:
        """Return matches for a task."""
        if not file or file.kind != "playbook":
            return []

        run_once = task.get("run_once", False)
        if not run_once:
            return []
        return [
            self.create_matcherror(
                message="Using run_once may behave differently if strategy is set to free.",
                filename=file,
                tag=f"{self.id}[task]",
                lineno=task[LINE_NUMBER_KEY],
            ),
        ]


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    import pytest

    # pylint: disable=ungrouped-imports
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    @pytest.mark.parametrize(
        ("test_file", "failure"),
        (
            pytest.param("examples/playbooks/run-once-pass.yml", 0, id="pass"),
            pytest.param("examples/playbooks/run-once-fail.yml", 2, id="fail"),
        ),
    )
    def test_run_once(
        default_rules_collection: RulesCollection,
        test_file: str,
        failure: int,
    ) -> None:
        """Test rule matches."""
        results = Runner(test_file, rules=default_rules_collection).run()
        for result in results:
            assert result.rule.id == RunOnce().id
        assert len(results) == failure
