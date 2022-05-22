"""Output formatters."""
import hashlib
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Generic, List, Tuple, TypeVar, Union

import rich

from ansiblelint.config import options
from ansiblelint.version import __version__

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError

T = TypeVar("T", bound="BaseFormatter")  # type: ignore


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

        self._base_dir = base_dir if display_relative_path else None

    def _format_path(self, path: Union[str, Path]) -> Union[str, Path]:
        if not self._base_dir or not path:
            return path
        # Use os.path.relpath 'cause Path.relative_to() misbehaves
        return os.path.relpath(path, start=self._base_dir)

    def format(self, match: "MatchError") -> str:
        """Format a match error."""
        return str(match)

    @staticmethod
    def escape(text: str) -> str:
        """Escapes a string to avoid processing it as markup."""
        return rich.markup.escape(text)


class Formatter(BaseFormatter):  # type: ignore
    """Default output formatter of ansible-lint."""

    def format(self, match: "MatchError") -> str:
        _id = getattr(match.rule, "id", "000")
        result = f"[error_code]{_id}[/][dim]:[/] [error_title]{self.escape(match.message)}[/]"
        if match.tag:
            result += f" [dim][error_code]({self.escape(match.tag)})[/][/]"
        result += (
            "\n"
            f"[filename]{self._format_path(match.filename or '')}[/]:{match.position}"
        )
        if match.details:
            result += f" [dim]{match.details}[/]"
        result += "\n"
        return result


class QuietFormatter(BaseFormatter[Any]):
    """Brief output formatter for ansible-lint."""

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
            result += f": [dim]{match.message}[/]"

        if match.tag:
            result += f" [dim][error_code]({self.escape(match.tag)})[/][/]"
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
        if severity in ["VERY_LOW", "LOW"]:
            return "warning"
        if severity in ["INFO"]:
            return "debug"
        # ['MEDIUM', 'HIGH', 'VERY_HIGH'] or anything else
        return "error"


class CodeclimateJSONFormatter(BaseFormatter[Any]):
    """Formatter for emitting violations in Codeclimate JSON report format.

    The formatter expects a list of MatchError objects and returns a JSON formatted string.
    The spec for the codeclimate report can be found here:
    https://github.com/codeclimate/platform/blob/master/spec/analyzers/SPEC.md#user-content-data-types
    """

    def format_result(self, matches: List["MatchError"]) -> str:
        """Format a list of match errors as a JSON string."""
        if not isinstance(matches, list):
            raise RuntimeError(
                f"The {self.__class__} was expecting a list of MatchError."
            )

        result = []
        for match in matches:
            issue: Dict[str, Any] = {}
            issue["type"] = "issue"
            issue["check_name"] = match.tag or match.rule.id  # rule-id[subrule-id]
            issue["categories"] = match.rule.tags
            issue["severity"] = self._severity_to_level(match.rule.severity)
            issue["description"] = self.escape(str(match.message))
            issue["fingerprint"] = hashlib.sha256(
                repr(match).encode("utf-8")
            ).hexdigest()
            issue["location"] = {}
            issue["location"]["path"] = self._format_path(match.filename or "")
            issue["location"]["lines"] = {}
            if match.column:
                issue["location"]["lines"]["begin"] = {}
                issue["location"]["lines"]["begin"]["line"] = match.linenumber
                issue["location"]["lines"]["begin"]["column"] = match.column
            else:
                issue["location"]["lines"]["begin"] = match.linenumber
            if match.details:
                issue["content"] = {}
                issue["content"]["body"] = match.details
            # Append issue to result list
            result.append(issue)

        return json.dumps(result)

    @staticmethod
    def _severity_to_level(severity: str) -> str:
        if severity in ["LOW"]:
            return "minor"
        if severity in ["MEDIUM"]:
            return "major"
        if severity in ["HIGH"]:
            return "critical"
        if severity in ["VERY_HIGH"]:
            return "blocker"
        # VERY_LOW, INFO or anything else
        return "info"


class SarifFormatter(BaseFormatter[Any]):
    """Formatter for emitting violations in SARIF report format.

    The spec of SARIF can be found here:
    https://docs.oasis-open.org/sarif/sarif/v2.1.0/
    """

    BASE_URI_ID = "SRCROOT"
    TOOL_NAME = "Ansible-lint"
    TOOL_URL = "https://github.com/ansible/ansible-lint"
    SARIF_SCHEMA_VERSION = "2.1.0"
    RULE_DOC_URL = "https://ansible-lint.readthedocs.io/en/latest/default_rules/"
    SARIF_SCHEMA = (
        "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0-rtm.5.json"
    )

    def format_result(self, matches: List["MatchError"]) -> str:
        """Format a list of match errors as a JSON string."""
        if not isinstance(matches, list):
            raise RuntimeError(
                f"The {self.__class__} was expecting a list of MatchError."
            )

        root_path = Path(str(self._base_dir)).as_uri()
        root_path = root_path + "/" if not root_path.endswith("/") else root_path
        rules, results = self._extract_results(matches)

        tool = {
            "driver": {
                "name": self.TOOL_NAME,
                "version": __version__,
                "informationUri": self.TOOL_URL,
                "rules": rules,
            }
        }

        runs = [
            {
                "tool": tool,
                "columnKind": "utf16CodeUnits",
                "results": results,
                "originalUriBaseIds": {
                    self.BASE_URI_ID: {"uri": root_path},
                },
            }
        ]

        report = {
            "$schema": self.SARIF_SCHEMA,
            "version": self.SARIF_SCHEMA_VERSION,
            "runs": runs,
        }

        return json.dumps(
            report, default=lambda o: o.__dict__, sort_keys=False, indent=2
        )

    def _extract_results(
        self, matches: List["MatchError"]
    ) -> Tuple[List[Any], List[Any]]:
        rules = {}
        results = []
        for match in matches:
            if match.rule.id not in rules:
                rules[match.rule.id] = self._to_sarif_rule(match)
            results.append(self._to_sarif_result(match))
        return list(rules.values()), results

    def _to_sarif_rule(self, match: "MatchError") -> Dict[str, Any]:
        rule: Dict[str, Any] = {
            "id": match.rule.id,
            "name": match.rule.id,
            "shortDescription": {
                "text": self.escape(str(match.message)),
            },
            "defaultConfiguration": {
                "level": self._to_sarif_level(match.rule.severity),
            },
            "help": {
                "text": str(match.rule.description),
            },
            "helpUri": self.RULE_DOC_URL + "#" + match.rule.id,
            "properties": {"tags": match.rule.tags},
        }
        if match.rule.link:
            rule["helpUri"] = match.rule.link
        return rule

    def _to_sarif_result(self, match: "MatchError") -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "ruleId": match.rule.id,
            "message": {
                "text": match.details,
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": self._format_path(match.filename or ""),
                            "uriBaseId": self.BASE_URI_ID,
                        },
                        "region": {
                            "startLine": match.linenumber,
                        },
                    },
                },
            ],
        }
        if match.column:
            result["locations"][0]["physicalLocation"]["region"][
                "startColumn"
            ] = match.column
        return result

    @staticmethod
    def _to_sarif_level(severity: str) -> str:
        if severity in ["VERY_HIGH", "HIGH", "MEDIUM"]:
            return "error"
        if severity in ["LOW"]:
            return "warning"
        # VERY_LOW, INFO or anything else
        return "note"
