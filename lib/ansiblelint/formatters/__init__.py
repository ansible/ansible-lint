"""Output formatters."""
import os
from pathlib import Path
from typing import TYPE_CHECKING, Generic, TypeVar, Union

from ansiblelint.color import Color, colorize

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

    def format(self, match: "MatchError", colored: bool = False) -> str:
        return str(match)


class Formatter(BaseFormatter):

    def format(self, match: "MatchError", colored: bool = False) -> str:
        formatstr = u"{0} {1}\n{2}:{3}\n{4}\n"
        _id = getattr(match.rule, 'id', '000')
        if colored:
            return formatstr.format(
                colorize(u"[{0}]".format(_id), Color.error_code),
                colorize(match.message, Color.error_title),
                colorize(self._format_path(match.filename or ""), Color.filename),
                colorize(str(match.linenumber), Color.linenumber),
                colorize(u"{0}".format(match.details), Color.line))
        else:
            return formatstr.format(_id,
                                    match.message,
                                    match.filename or "",
                                    match.linenumber,
                                    match.details)


class QuietFormatter(BaseFormatter):

    def format(self, match: "MatchError", colored: bool = False) -> str:
        formatstr = u"{0} {1}:{2}"
        if colored:
            return formatstr.format(
                colorize(u"[{0}]".format(match.rule.id), Color.error_code),
                colorize(self._format_path(match.filename or ""), Color.filename),
                colorize(str(match.linenumber), Color.linenumber))
        else:
            return formatstr.format(match.rule.id, self._format_path(match.filename or ""),
                                    match.linenumber)


class ParseableFormatter(BaseFormatter):

    def format(self, match: "MatchError", colored: bool = False) -> str:
        formatstr = u"{0}:{1}: [{2}] {3}"
        if colored:
            return formatstr.format(
                colorize(self._format_path(match.filename or ""), Color.filename),
                colorize(str(match.linenumber), Color.linenumber),
                colorize(u"E{0}".format(match.rule.id), Color.error_code),
                colorize(u"{0}".format(match.message), Color.error_title))
        else:
            return formatstr.format(self._format_path(match.filename or ""),
                                    match.linenumber,
                                    "E" + match.rule.id,
                                    match.message)


class AnnotationsFormatter(BaseFormatter):
    # https://docs.github.com/en/actions/reference/workflow-commands-for-github-actions#setting-a-warning-message
    """Formatter for emitting violations as GitHub Workflow Commands.

    These commands trigger the GHA Workflow runners platform to post violations
    in a form of GitHub Checks API annotations that appear rendered in pull-
    request files view.

    ::debug file={name},line={line},col={col}::{message}
    ::warning file={name},line={line},col={col}::{message}
    ::error file={name},line={line},col={col}::{message}

    Supported levels: debug, warning, error
    """

    def format(self, match: "MatchError", colored: bool = False) -> str:
        """Prepare a match instance for reporting as a GitHub Actions annotation."""
        if colored:
            raise ValueError('The colored mode is not supported.')

        level = self._severity_to_level(match.rule.severity)
        file_path = self._format_path(match.filename or "")
        line_num = match.linenumber
        rule_id = match.rule.id
        violation_details = match.message
        return (
            f"::{level} file={file_path},line={line_num}"
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

    def format(self, match: "MatchError", colored: bool = False) -> str:
        formatstr = u"{0}:{1}: [{2}] [{3}] {4}"

        filename = self._format_path(match.filename or "")
        linenumber = str(match.linenumber)
        rule_id = u"E{0}".format(match.rule.id)
        severity = match.rule.severity
        message = str(match.message)

        if colored:
            filename = colorize(filename, Color.filename)
            linenumber = colorize(linenumber, Color.linenumber)
            rule_id = colorize(rule_id, Color.error_code)
            severity = colorize(severity, Color.error_code)
            message = colorize(message, Color.error_title)

        return formatstr.format(
            filename,
            linenumber,
            rule_id,
            severity,
            message,
        )
