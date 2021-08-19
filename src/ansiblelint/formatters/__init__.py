"""Output formatters."""
import hashlib
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Generic, List, TypeVar, Union

import rich

from ansiblelint.config import options

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError

T = TypeVar('T', bound='BaseFormatter')  # type: ignore


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

        if not self._base_dir or not path:
            return path
        # Use os.path.relpath 'cause Path.relative_to() misbehaves
        return os.path.relpath(path, start=self._base_dir)

    def format(self, match: "MatchError") -> str:
        return str(match)

    def escape(self, text: str) -> str:
        """Escapes a string to avoid processing it as markup."""
        return rich.markup.escape(text)


class Formatter(BaseFormatter):  # type: ignore
    def format(self, match: "MatchError") -> str:
        _id = getattr(match.rule, 'id', '000')
        result = f"[error_code]{_id}[/][dim]:[/] [error_title]{self.escape(match.message)}[/]"
        if match.tag:
            result += f" [dim][error_code]({match.tag})[/][/]"
        result += (
            "\n"
            f"[filename]{self._format_path(match.filename or '')}[/]:{match.position}"
        )
        if match.details:
            result += f" [dim]{match.details}[/]"
        result += "\n"
        return result


class QuietFormatter(BaseFormatter[Any]):
    def format(self, match: "MatchError") -> str:
        return (
            f"[error_code]{match.rule.id}[/] "
            f"[filename]{self._format_path(match.filename or '')}[/]:{match.position}"
        )


class ParseableFormatter(BaseFormatter[Any]):
    """Parseable uses PEP8 compatible format."""

    def format(self, match: "MatchError") -> str:
        result = (
            f"[filename]{self._format_path(match.filename or '')}[/]:{match.position}: "
            f"[error_code]{match.rule.id}[/]"
        )

        if not options.quiet:
            result += f" [dim]{match.message}[/]"

        if match.tag:
            result += f" [dim][error_code]({match.tag})[/][/]"
        return result


class AnnotationsFormatter(BaseFormatter):  # type: ignore
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
        violation_details = self.escape(match.message)
        if match.column:
            col = f",col={match.column}"
        else:
            col = ""
        return (
            f"::{level} file={file_path},line={line_num}{col},severity={severity}"
            f"::{rule_id} {violation_details}"
        )

    @staticmethod
    def _severity_to_level(severity: str) -> str:
        if severity in ['VERY_LOW', 'LOW']:
            return 'warning'
        if severity in ['INFO']:
            return 'debug'
        # ['MEDIUM', 'HIGH', 'VERY_HIGH'] or anything else
        return 'error'


class ParseableSeverityFormatter(BaseFormatter[Any]):
    def format(self, match: "MatchError") -> str:

        filename = self._format_path(match.filename or "")
        position = match.position
        rule_id = u"{0}".format(match.rule.id)
        severity = match.rule.severity
        message = self.escape(str(match.message))

        return (
            f"[filename]{filename}[/]:{position}: [[error_code]{rule_id}[/]] "
            f"[[error_code]{severity}[/]] [dim]{message}[/]"
        )


class CodeclimateJSONFormatter(BaseFormatter[Any]):
    """Formatter for emitting violations in Codeclimate JSON report format.

    The formatter expects a list of MatchError objects and returns a JSON formatted string.
    The spec for the codeclimate report can be found here:
    https://github.com/codeclimate/platform/blob/master/spec/analyzers/SPEC.md#user-content-data-types
    """

    def format_result(self, matches: List["MatchError"]) -> str:

        if not isinstance(matches, list):
            raise RuntimeError(
                "The CodeclimatJSONFormatter was expecting a list of MatchError."
            )

        result = []
        for match in matches:
            issue: Dict[str, Any] = {}
            issue['type'] = 'issue'
            issue['check_name'] = f"[{match.rule.id}] {match.message}"
            issue['categories'] = match.rule.tags
            issue['severity'] = self._severity_to_level(match.rule.severity)
            issue['description'] = self.escape(str(match.rule.description))
            issue['fingerprint'] = hashlib.sha256(
                repr(match).encode('utf-8')
            ).hexdigest()
            issue['location'] = {}
            issue['location']['path'] = self._format_path(match.filename or "")
            issue['location']['lines'] = {}
            if match.column:
                issue['location']['lines']['begin'] = {}
                issue['location']['lines']['begin']['line'] = match.linenumber
                issue['location']['lines']['begin']['column'] = match.column
            else:
                issue['location']['lines']['begin'] = match.linenumber
            if match.details:
                issue['content'] = {}
                issue['content']['body'] = match.details
            # Append issue to result list
            result.append(issue)

        return json.dumps(result)

    @staticmethod
    def _severity_to_level(severity: str) -> str:
        if severity in ['LOW']:
            return 'minor'
        if severity in ['MEDIUM']:
            return 'major'
        if severity in ['HIGH']:
            return 'critical'
        if severity in ['VERY_HIGH']:
            return 'blocker'
        # VERY_LOW, INFO or anything else
        return 'info'
