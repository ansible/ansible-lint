"""Implementation of no-prompting rule."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from ansiblelint.constants import LINE_NUMBER_KEY
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.config import Options
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task


class NoPromptingRule(AnsibleLintRule):
    """Disallow prompting."""

    id = "no-prompting"
    description = (
        "Disallow the use of vars_prompt or ansible.builtin.pause to better"
        "accommodate unattended playbook runs and use in CI pipelines."
    )
    tags = ["opt-in"]
    severity = "VERY_LOW"
    version_added = "v6.0.3"

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        """Return matches found for a specific playbook."""
        # If the Play uses the 'vars_prompt' section to set variables

        if file.kind != "playbook":  # pragma: no cover
            return []

        vars_prompt = data.get("vars_prompt")
        if not vars_prompt:
            return []
        return [
            self.create_matcherror(
                message="Play uses vars_prompt",
                lineno=vars_prompt[0][LINE_NUMBER_KEY],
                filename=file,
            ),
        ]

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> bool | str:
        """Return matches for ansible.builtin.pause tasks."""
        # We do not want to trigger this rule if pause has either seconds or
        # minutes defined, as that does not make it blocking.
        return task["action"]["__ansible_module_original__"] in [
            "pause",
            "ansible.builtin.pause",
        ] and not (
            task["action"].get("minutes", None) or task["action"].get("seconds", None)
        )


if "pytest" in sys.modules:
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    def test_no_prompting_fail(config_options: Options) -> None:
        """Negative test for no-prompting."""
        # For testing we want to manually enable opt-in rules
        config_options.enable_list = ["no-prompting"]
        rules = RulesCollection(options=config_options)
        rules.register(NoPromptingRule())
        results = Runner("examples/playbooks/rule-no-prompting.yml", rules=rules).run()
        assert len(results) == 2
        for result in results:
            assert result.rule.id == "no-prompting"
