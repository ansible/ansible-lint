"""Output formatters."""
from __future__ import annotations

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

    def __init__(self, base_dir: str | Path, display_relative_path: bool) -> None:
        """Initialize a BaseFormatter instance."""
        if isinstance(base_dir, str):
            base_dir = Path(base_dir)
        if base_dir:  # can be None
            base_dir = base_dir.absolute()

        self._base_dir = base_dir if display_relative_path else None

    def _format_path(self, path: str | Path) -> str | Path:
        if not self._base_dir or not path:
            return path
        # Use os.path.relpath 'cause Path.relative_to() misbehaves
        return os.path.relpath(path, start=self._base_dir)

    def format(self, match: MatchError) -> str:
        """Format a match error."""
        return str(match)

    @staticmethod
    def escape(text: str) -> str:
        """Escapes a string to avoid processing it as markup."""
        return rich.markup.escape(text)


class Formatter(BaseFormatter):  # type: ignore
    """Default output formatter of ansible-lint."""

    def format(self, match: MatchError) -> str:
        _id = getattr(match.rule, "id", "000")
        result = f"[{match.level}][bold][link={match.rule.url}]{self.escape(match.tag)}[/link][/][/][dim]:[/] [{match.level}]{self.escape(match.message)}[/]"
        if match.level != "error":
            result += f" [dim][{match.level}]({match.level})[/][/]"
        result += (
            "\n"
            f"[filename]{self._format_path(match.filename or '')}[/]:{match.position}"
        )
        if match.details:
            result += f" [dim]{self.escape(str(match.details))}[/]"
        result += "\n"
        return result


class QuietFormatter(BaseFormatter[Any]):
    """Brief output formatter for ansible-lint."""

    def format(self, match: MatchError) -> str:
        return (
            f"[{match.level}]{match.rule.id}[/] "
            f"[filename]{self._format_path(match.filename or '')}[/]:{match.position}"
        )


class ParseableFormatter(BaseFormatter[Any]):
    """Parseable uses PEP8 compatible format."""

    def format(self, match: MatchError) -> str:
        result = (
            f"[filename]{self._format_path(match.filename or '')}[/][dim]:{match.position}:[/] "
            f"[{match.level}][bold]{self.escape(match.tag)}[/bold]"
            f"{ f': {match.message}' if not options.quiet else '' }[/]"
        )
        if match.level != "error":
            result += f" [dim][{match.level}]({match.level})[/][/]"

        return result


class AnnotationsFormatter(BaseFormatter):  # type: ignore
    # https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#setting-a-warning-message
    """Formatter for emitting violations as GitHub Workflow Commands.

    These commands trigger the GHA Workflow runners platform to post violations
    in a form of GitHub Checks API annotations that appear rendered in pull-
    request files view.

    ::debug file={name},line={line},col={col},severity={severity}::{message}
    ::warning file={name},line={line},col={col},severity={severity}::{message}
    ::error file={name},line={line},col={col},severity={severity}::{message}

    Supported levels: debug, warning, error
    """

    def format(self, match: MatchError) -> str:
        """Prepare a match instance for reporting as a GitHub Actions annotation."""
        file_path = self._format_path(match.filename or "")
        line_num = match.linenumber
        severity = match.rule.severity
        violation_details = self.escape(match.message)
        if match.column:
            col = f",col={match.column}"
        else:
            col = ""
        return (
            f"::{match.level} file={file_path},line={line_num}{col},severity={severity},title={match.tag}"
            f"::{violation_details}"
        )


class CodeclimateJSONFormatter(BaseFormatter[Any]):
    """Formatter for emitting violations in Codeclimate JSON report format.

    The formatter expects a list of MatchError objects and returns a JSON formatted string.
    The spec for the codeclimate report can be found here:
    https://github.com/codeclimate/platform/blob/master/spec/analyzers/SPEC.md#user-content-data-types
    """

    def format_result(self, matches: list[MatchError]) -> str:
        """Format a list of match errors as a JSON string."""
        if not isinstance(matches, list):
            raise RuntimeError(
                f"The {self.__class__} was expecting a list of MatchError."
            )

        result = []
        for match in matches:
            issue: dict[str, Any] = {}
            issue["type"] = "issue"
            issue["check_name"] = match.tag or match.rule.id  # rule-id[subrule-id]
            issue["categories"] = match.rule.tags
            if match.rule.url:
                # https://github.com/codeclimate/platform/issues/68
                issue["url"] = match.rule.url
            issue["severity"] = self._remap_severity(match)
            # level is not part of CodeClimate specification, but there is
            # no other way to expose that info. We recommend switching to
            # SARIF format which is better suited for interoperability.
            issue["level"] = match.level
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
    def _remap_severity(match: MatchError) -> str:
        severity = match.rule.severity

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
    TOOL_NAME = "ansible-lint"
    TOOL_URL = "https://github.com/ansible/ansible-lint"
    SARIF_SCHEMA_VERSION = "2.1.0"
    SARIF_SCHEMA = (
        "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0-rtm.5.json"
    )

    def format_result(self, matches: list[MatchError]) -> str:
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
        self, matches: list[MatchError]
    ) -> tuple[list[Any], list[Any]]:
        rules = {}
        results = []
        for match in matches:
            if match.tag not in rules:
                rules[match.tag] = self._to_sarif_rule(match)
            results.append(self._to_sarif_result(match))
        return list(rules.values()), results

    def _to_sarif_rule(self, match: MatchError) -> dict[str, Any]:
        rule: dict[str, Any] = {
            "id": match.tag,
            "name": match.tag,
            "shortDescription": {
                "text": str(match.message),
            },
            "defaultConfiguration": {
                "level": self._to_sarif_level(match),
            },
            "help": {
                "text": str(match.rule.description),
            },
            "helpUri": match.rule.url,
            "properties": {"tags": match.rule.tags},
        }
        if match.rule.link:
            rule["helpUri"] = match.rule.link
        return rule

    def _to_sarif_result(self, match: MatchError) -> dict[str, Any]:
        result: dict[str, Any] = {
            "ruleId": match.tag,
            "message": {
                "text": str(match.message),
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
    def _to_sarif_level(match: MatchError) -> str:
        # sarif accepts only 4 levels: error, warning, note, none
        return match.level
