from typing import TYPE_CHECKING, List, Union

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable


class BaseRule:
    """Root class used by Rules."""

    id: str = ""
    tags: List[str] = []
    shortdesc: str = ""
    description: str = ""
    version_added: str = ""
    severity: str = ""
    matchtask = None

    def matchlines(self, file: "Lintable") -> List["MatchError"]:
        """Return matches found for a specific line."""
        return []

    def matchtasks(self, file: "Lintable") -> List["MatchError"]:
        """Return matches for a tasks file."""
        return []

    def matchyaml(self, file: "Lintable") -> List["MatchError"]:
        """Return matches found for a specific YAML text."""
        return []

    def matchplay(self, file: "Lintable", data) -> List["MatchError"]:
        """Return matches found for a specific playbook."""
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

    id = '999'
    shortdesc = 'Unexpected internal error'
    description = (
        'This error can be caused by internal bugs but also by '
        'custom rules. Instead of just stopping linter we generate there errors and '
        'continue processing. This allows users to add this rule to warn list until '
        'the root cause is fixed.')
    severity = 'VERY_HIGH'
    tags = ['core']
    version_added = 'v5.0.0'


class AnsibleParserErrorRule(BaseRule):
    """Used to mark errors received from Ansible."""

    id = '998'
    shortdesc = 'AnsibleParserError'
    description = (
        'Ansible parser fails, this usually indicate invalid file.')
    severity = 'VERY_HIGH'
    tags = ['core']
    version_added = 'v5.0.0'


class LoadingFailureRule(BaseRule):
    """File loading failure."""

    id = '901'
    shortdesc = 'Failed to load or parse file'
    description = 'Linter failed to process a YAML file, possible not an Ansible file.'
    severity = 'VERY_HIGH'
    tags = ['core']
    version_added = 'v4.3.0'
