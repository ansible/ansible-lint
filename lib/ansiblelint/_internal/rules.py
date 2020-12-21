from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError


class BaseRule:
    """Root class used by Rules."""

    id: str = ""
    tags: List[str] = []
    shortdesc: str = ""
    description: str = ""
    version_added: str = ""
    severity: str = ""
    match = None
    matchtask = None
    matchplay = None

    def matchlines(self, file, text) -> List["MatchError"]:
        """Return matches found for a specific line."""
        return []

    def matchtasks(self, file: str, text: str) -> List["MatchError"]:
        """Return matches for a tasks file."""
        return []

    def matchyaml(self, file: str, text: str) -> List["MatchError"]:
        """Return matches found for a specific YAML text."""
        return []

    def verbose(self) -> str:
        """Return a verbose representation of the rule."""
        return self.id + ": " + self.shortdesc + "\n  " + self.description


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
