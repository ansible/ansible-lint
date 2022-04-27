"""Implementation of no-prompting rule."""

from typing import TYPE_CHECKING, Any, Dict, List, Union

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.utils import LINE_NUMBER_KEY

if TYPE_CHECKING:
    from typing import Optional

    from ansiblelint.constants import odict
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable


class NoPromptingRule(AnsibleLintRule):
    """Disallow prompting."""

    id = "no-prompting"
    description = (
        "Disallow the use of vars_prompt or ansible.builtin.pause to better"
        "accommodate unattended playbook runs and use in CI pipelines."
    )
    tags = ["opt-in", "experimental"]
    severity = "VERY_LOW"
    version_added = "v6.0.3"

    def matchplay(
        self, file: "Lintable", data: "odict[str, Any]"
    ) -> List["MatchError"]:
        """Return matches found for a specific playbook."""
        # If the Play uses the 'vars_prompt' section to set variables

        if file.kind != "playbook":
            return []

        vars_prompt = data.get("vars_prompt", None)
        if not vars_prompt:
            return []

        return [
            self.create_matcherror(
                message="Play uses vars_prompt",
                linenumber=vars_prompt[LINE_NUMBER_KEY],
                filename=file,
            )
        ]

    def matchtask(
        self, task: Dict[str, Any], file: "Optional[Lintable]" = None
    ) -> Union[bool, str]:
        """Return matches for ansible.builtin.pause tasks."""
        return task["action"]["__ansible_module_original__"] in [
            "pause",
            "ansible.builtin.pause",
        ]
