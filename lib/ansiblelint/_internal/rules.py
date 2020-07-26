from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import TargetFile


class BaseRule:
    """Root class used by Rules."""

    id: str = ""
    tags: List[str] = []
    shortdesc: str = ""
    description: str = ""
    version_added: str = ""
    severity: str = ""
    matchtask = None
    matchplay = None

    def match(self, file: "TargetFile", line: str, line_no: Optional[int]) -> List["MatchError"]:
        """Return matches found for a specific line with line_no."""
        return []

    def matchlines(self, file: "TargetFile", text: str) -> List["MatchError"]:
        """Return matches found for a specific line."""
        return []

    def matchtasks(self, file: "TargetFile", text: str) -> List["MatchError"]:
        """Return matches for a tasks file."""
        return []

    def matchyaml(self, file: "TargetFile", text: str) -> List["MatchError"]:
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
