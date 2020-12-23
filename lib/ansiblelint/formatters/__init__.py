"""Output formatters."""
import os
from pathlib import Path
from typing import TYPE_CHECKING, Generic, TypeVar, Union

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError

T = TypeVar('T', bound='BaseFormatter')


class BaseFormatter(Generic[T]):
    """Formatter of ansible-lint output.

    Base class for output formatters.

    Args:
        base_dir (str|Path): reference directory against which display relative path.
        display_relative_path (bool): whether to show path as relative or absolute
    """

    def __init__(self, base_dir: Union[str, Path], display_relative_path: bool) -> None:
        """Initialize a BaseFormatter instance."""
        if isinstance(base_dir, str):
            base_dir = Path(base_dir)
        if base_dir:  # can be None
            base_dir = base_dir.absolute()

        # Required 'cause os.path.relpath() does not accept Path before 3.6
        if isinstance(base_dir, Path):
            base_dir = str(base_dir)  # Drop when Python 3.5 is no longer supported

        self._base_dir = base_dir if display_relative_path else None

    def _format_path(self, path: Union[str, Path]) -> str:
        # Required 'cause os.path.relpath() does not accept Path before 3.6
        if isinstance(path, Path):
            path = str(path)  # Drop when Python 3.5 is no longer supported

        if not self._base_dir:
            return path
        # Use os.path.relpath 'cause Path.relative_to() misbehaves
        return os.path.relpath(path, start=self._base_dir)

    def format(self, match: "MatchError") -> str:
        return str(match)


class Formatter(BaseFormatter):

    def format(self, match: "MatchError") -> str:
        _id = getattr(match.rule, 'id', '000')
        return (
            f"[error_code]{_id}[/] [error_title]{match.message}[/]\n"
            f"[filename]{self._format_path(match.filename or '')}[/]:{match.linenumber}\n"
            f"[dim]{match.details}[/]\n")


class QuietFormatter(BaseFormatter):

    def format(self, match: "MatchError") -> str:
        return (
            f"[error_code]{match.rule.id}[/] "
            f"[filename]{self._format_path(match.filename or '')}[/]:{match.linenumber}")


class ParseableFormatter(BaseFormatter):

    def format(self, match: "MatchError") -> str:
        return (
            f"[filename]{self._format_path(match.filename or '')}[/]:{match.linenumber}: "
            f"[[error_code]E{match.rule.id}[/]] [dim]{match.message}[/]")


class AnnotationsFormatter(BaseFormatter):
    # https://docs.github.com/en/actions/reference/workflow-commands-for-github-actions#setting-a-warning-message
    """Formatter for emitting violations as GitHub Workflow Commands.

    These commands trigger the GHA Workflow runners platform to post violations
    in a form of GitHub Checks API annotations that appear rendered in pull-
    request files view.

    ::debug file={name},line={line},col={col},severity={severity}::{message}
    ::warning file={name},line={line},col={col},severity={severity}::{message}
    ::error file={name},line={line},col={col},severity={severity}::{message}

    Supported levels: debug, warning, error
    """

    def format(self, match: "MatchError") -> str:
        """Prepare a match instance for reporting as a GitHub Actions annotation."""
        level = self._severity_to_level(match.rule.severity)
        file_path = self._format_path(match.filename or "")
        line_num = match.linenumber
        rule_id = match.rule.id
        severity = match.rule.severity
        violation_details = match.message
        return (
            f"::{level} file={file_path},line={line_num},severity={severity}"
            f"::[E{rule_id}] {violation_details}"
        )

    @staticmethod
    def _severity_to_level(severity: str) -> str:
        if severity in ['VERY_LOW', 'LOW']:
            return 'warning'
        elif severity in ['INFO']:
            return 'debug'
        # ['MEDIUM', 'HIGH', 'VERY_HIGH'] or anything else
        return 'error'


class ParseableSeverityFormatter(BaseFormatter):

    def format(self, match: "MatchError") -> str:

        filename = self._format_path(match.filename or "")
        linenumber = str(match.linenumber)
        rule_id = u"E{0}".format(match.rule.id)
        severity = match.rule.severity
        message = str(match.message)

        return (
            f"[filename]{filename}[/]:{linenumber}: [[error_code]{rule_id}[/]] "
            f"[[error_code]{severity}[/]] [dim]{message}[/]")
