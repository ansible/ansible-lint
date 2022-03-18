"""Implementation of no-jinja-when rule."""
from typing import TYPE_CHECKING, Any, Dict, List, Union

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.utils import LINE_NUMBER_KEY

if TYPE_CHECKING:
    from typing import Optional

    from ansiblelint.constants import odict
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable


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
        if not isinstance(when, str):
            return True
        return when.find("{{") == -1 and when.find("}}") == -1

    def matchplay(
        self, file: "Lintable", data: "odict[str, Any]"
    ) -> List["MatchError"]:
        errors: List["MatchError"] = []
        if isinstance(data, dict):
            if "roles" not in data or data["roles"] is None:
                return errors
            for role in data["roles"]:
                if self.matchtask(role, file=file):
                    errors.append(
                        self.create_matcherror(
                            details=str({"when": role}),
                            filename=file,
                            linenumber=role[LINE_NUMBER_KEY],
                        )
                    )
        if isinstance(data, list):
            for play_item in data:
                sub_errors = self.matchplay(file, play_item)
                if sub_errors:
                    errors = errors + sub_errors
        return errors

    def matchtask(
        self, task: Dict[str, Any], file: "Optional[Lintable]" = None
    ) -> Union[bool, str]:
        return "when" in task and not self._is_valid(task["when"])
