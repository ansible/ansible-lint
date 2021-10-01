import logging
from typing import TYPE_CHECKING, Any, Dict, List, Union

if TYPE_CHECKING:
    from typing import Optional

    from ansiblelint.constants import odict
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable

_logger = logging.getLogger(__name__)


class BaseRule:
    """Root class used by Rules."""

    id: str = ""
    tags: List[str] = []
    shortdesc: str = ""
    description: str = ""
    version_added: str = ""
    severity: str = ""
    link: str = ""
    has_dynamic_tags: bool = False

    def getmatches(self, file: "Lintable") -> List["MatchError"]:
        """Return all matches while ignoring exceptions."""
        matches = []
        if not file.path.is_dir():
            for method in [self.matchlines, self.matchtasks, self.matchyaml]:
                try:
                    matches.extend(method(file))
                except Exception as e:
                    _logger.debug(
                        "Ignored exception from %s.%s: %s",
                        self.__class__.__name__,
                        method,
                        e,
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
        """Confirm if current rule is matching a specific task."""
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


class RuntimeErrorRule(BaseRule):
    """Used to identify errors."""

    id = 'internal-error'
    shortdesc = 'Unexpected internal error'
    description = (
        'This error can be caused by internal bugs but also by '
        'custom rules. Instead of just stopping linter we generate there errors and '
        'continue processing. This allows users to add this rule to warn list until '
        'the root cause is fixed.'
    )
    severity = 'VERY_HIGH'
    tags = ['core']
    version_added = 'v5.0.0'


class AnsibleParserErrorRule(BaseRule):
    """Used to mark errors received from Ansible."""

    id = 'parser-error'
    shortdesc = 'AnsibleParserError'
    description = 'Ansible parser fails; this usually indicates an invalid file.'
    severity = 'VERY_HIGH'
    tags = ['core']
    version_added = 'v5.0.0'


class LoadingFailureRule(BaseRule):
    """File loading failure."""

    id = 'load-failure'
    shortdesc = 'Failed to load or parse file'
    description = 'Linter failed to process a YAML file, possible not an Ansible file.'
    severity = 'VERY_HIGH'
    tags = ['core']
    version_added = 'v4.3.0'
