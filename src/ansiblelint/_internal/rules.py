"""Internally used rule classes."""
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Union

if TYPE_CHECKING:
    from typing import Optional

    from ansiblelint.constants import odict
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable

_logger = logging.getLogger(__name__)


# Derived rules are likely to want to access class members, so:
# pylint: disable=unused-argument
class BaseRule:
    """Root class used by Rules."""

    id: str = ""
    tags: List[str] = []
    description: str = ""
    help: str = ""  # markdown help (automatically loaded from `<rule>.md`)
    version_added: str = ""
    severity: str = ""
    link: str = ""
    has_dynamic_tags: bool = False
    needs_raw_task: bool = False

    @property
    def shortdesc(self) -> str:
        """Return the short description of the rule, basically the docstring."""
        return self.__doc__ or ""

    def getmatches(self, file: "Lintable") -> List["MatchError"]:
        """Return all matches while ignoring exceptions."""
        matches = []
        if not file.path.is_dir():
            for method in [self.matchlines, self.matchtasks, self.matchyaml]:
                try:
                    matches.extend(method(file))
                except Exception as exc:  # pylint: disable=broad-except
                    _logger.debug(
                        "Ignored exception from %s.%s: %s",
                        self.__class__.__name__,
                        method,
                        exc,
                    )
        else:
            matches.extend(self.matchdir(file))
        return matches

    def matchlines(self, file: "Lintable") -> List["MatchError"]:
        """Return matches found for a specific line."""
        return []

    def matchtask(
        self, task: Dict[str, Any], file: "Optional[Lintable]" = None
    ) -> Union[bool, str]:
        """Confirm if current rule is matching a specific task.

        If ``needs_raw_task`` (a class level attribute) is ``True``, then
        the original task (before normalization) will be made available under
        ``task["__raw_task__"]``.
        """
        return False

    def matchtasks(self, file: "Lintable") -> List["MatchError"]:
        """Return matches for a tasks file."""
        return []

    def matchyaml(self, file: "Lintable") -> List["MatchError"]:
        """Return matches found for a specific YAML text."""
        return []

    def matchplay(
        self, file: "Lintable", data: "odict[str, Any]"
    ) -> List["MatchError"]:
        """Return matches found for a specific playbook."""
        return []

    def matchdir(self, lintable: "Lintable") -> List["MatchError"]:
        """Return matches for lintable folders."""
        return []

    def verbose(self) -> str:
        """Return a verbose representation of the rule."""
        return self.id + ": " + self.shortdesc + "\n  " + self.description

    def match(self, line: str) -> Union[bool, str]:
        """Confirm if current rule matches the given string."""
        return False

    def __lt__(self, other: "BaseRule") -> bool:
        """Enable us to sort rules by their id."""
        return self.id < other.id


# pylint: enable=unused-argument


class RuntimeErrorRule(BaseRule):
    """Unexpected internal error."""

    id = "internal-error"
    description = (
        "This error can be caused by internal bugs but also by "
        "custom rules. Instead of just stopping linter we generate the errors and "
        "continue processing. This allows users to add this rule to their warn list until "
        "the root cause is fixed."
    )
    severity = "VERY_HIGH"
    tags = ["core"]
    version_added = "v5.0.0"


class AnsibleParserErrorRule(BaseRule):
    """AnsibleParserError."""

    id = "parser-error"
    description = "Ansible parser fails; this usually indicates an invalid file."
    severity = "VERY_HIGH"
    tags = ["core"]
    version_added = "v5.0.0"


class LoadingFailureRule(BaseRule):
    """Failed to load or parse file."""

    id = "load-failure"
    description = "Linter failed to process a YAML file, possible not an Ansible file."
    severity = "VERY_HIGH"
    tags = ["core"]
    version_added = "v4.3.0"
