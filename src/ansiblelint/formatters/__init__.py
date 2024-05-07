"""Output formatters."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generic, TypeVar

import rich

from ansiblelint.config import options
from ansiblelint.version import __version__

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.rules import BaseRule  # type: ignore[attr-defined]

T = TypeVar("T", bound="BaseFormatter")  # type: ignore[type-arg]


class BaseFormatter(Generic[T]):
    """Formatter of ansible-lint output.

    Base class for output formatters.

    Args:
    ----
        base_dir (str|Path): reference directory against which display relative path.
        display_relative_path (bool): whether to show path as relative or absolute

    """

    def __init__(self, base_dir: str | Path, display_relative_path: bool) -> None:
        """Initialize a BaseFormatter instance."""
        if isinstance(base_dir, str):
            base_dir = Path(base_dir)
        if base_dir:  # can be None
            base_dir = base_dir.absolute()

        self.base_dir = base_dir if display_relative_path else None

    def _format_path(self, path: str | Path) -> str | Path:
        if not self.base_dir or not path:
            return path
        # Use os.path.relpath 'cause Path.relative_to() misbehaves
        rel_path = os.path.relpath(path, start=self.base_dir)
        # Avoid returning relative paths that go outside of base_dir
        if rel_path.startswith(".."):
            return path
        return rel_path

    def apply(self, match: MatchError) -> str:
        """Format a match error."""
        return str(match)

    @staticmethod
    def escape(text: str) -> str:
        """Escapes a string to avoid processing it as markup."""
        return rich.markup.escape(text)


class Formatter(BaseFormatter):  # type: ignore[type-arg]
    """Default output formatter of ansible-lint."""

    def apply(self, match: MatchError) -> str:
        _id = getattr(match.rule, "id", "000")
        result = f"[{match.level}][bold][link={match.rule.url}]{self.escape(match.tag)}[/link][/][/][dim]:[/] [{match.level}]{self.escape(match.message)}[/]"
        if match.level != "error":
            result += f" [dim][{match.level}]({match.level})[/][/]"
        if match.ignored:
            result += " [dim]# ignored[/]"
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

    def apply(self, match: MatchError) -> str:
        return (
            f"[{match.level}]{match.rule.id}[/] "
            f"[filename]{self._format_path(match.filename or '')}[/]:{match.position}"
        )


class ParseableFormatter(BaseFormatter[Any]):
    """Parseable uses PEP8 compatible format."""

    def apply(self, match: MatchError) -> str:
        result = (
            f"[filename]{self._format_path(match.filename or '')}[/][dim]:{match.position}:[/] "
            f"[{match.level}][bold]{self.escape(match.tag)}[/bold]"
            f"{ f': {match.message}' if not options.quiet else '' }[/]"
        )
        if match.level != "error":
            result += f" [dim][{match.level}]({match.level})[/][/]"

        return result


class AnnotationsFormatter(BaseFormatter):  # type: ignore[type-arg]
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

    def apply(self, match: MatchError) -> str:
        """Prepare a match instance for reporting as a GitHub Actions annotation."""
        file_path = self._format_path(match.filename or "")
        line_num = match.lineno
        severity = match.rule.severity
        violation_details = self.escape(match.message)
        col = f",col={match.column}" if match.column else ""
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
            msg = f"The {self.__class__} was expecting a list of MatchError."
            raise TypeError(msg)

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
            issue["description"] = self.escape(str(match.message))
            issue["fingerprint"] = hashlib.sha256(
                repr(match).encode("utf-8"),
            ).hexdigest()
            issue["location"] = {}
            issue["location"]["path"] = self._format_path(match.filename or "")
            if match.column:
                issue["location"]["positions"] = {}
                issue["location"]["positions"]["begin"] = {}
                issue["location"]["positions"]["begin"]["line"] = match.lineno
                issue["location"]["positions"]["begin"]["column"] = match.column
            else:
                issue["location"]["lines"] = {}
                issue["location"]["lines"]["begin"] = match.lineno
            if match.details:
                issue["content"] = {}
                issue["content"]["body"] = match.details
            # Append issue to result list
            result.append(issue)

        # Keep it single line due to https://github.com/ansible/ansible-navigator/issues/1490
        return json.dumps(result, sort_keys=False)

    @staticmethod
    def _remap_severity(match: MatchError) -> str:
        # level is not part of CodeClimate specification, but there is
        # no other way to expose that info. We recommend switching to
        # SARIF format which is better suited for interoperability.
        #
        # Out current implementation will return `major` for all errors and
        # `warning` for all warnings. We may revisit this in the future.
        if match.level == "warning":
            return "minor"
        return "major"


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
            msg = f"The {self.__class__} was expecting a list of MatchError."
            raise TypeError(msg)

        root_path = Path(str(self.base_dir)).as_uri()
        root_path = root_path + "/" if not root_path.endswith("/") else root_path
        rules, results = self._extract_results(matches)

        tool = {
            "driver": {
                "name": self.TOOL_NAME,
                "version": __version__,
                "informationUri": self.TOOL_URL,
                "rules": rules,
            },
        }

        runs = [
            {
                "tool": tool,
                "columnKind": "utf16CodeUnits",
                "results": results,
                "originalUriBaseIds": {
                    self.BASE_URI_ID: {"uri": root_path},
                },
            },
        ]

        report = {
            "$schema": self.SARIF_SCHEMA,
            "version": self.SARIF_SCHEMA_VERSION,
            "runs": runs,
        }
        # Keep it single line due to https://github.com/ansible/ansible-navigator/issues/1490
        return json.dumps(report, sort_keys=False)

    def _extract_results(
        self,
        matches: list[MatchError],
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
                "level": self.get_sarif_rule_severity_level(match.rule),
            },
            "help": {
                "text": str(match.rule.description),
            },
            "helpUri": match.rule.url,
            "properties": {"tags": match.rule.tags},
        }
        return rule

    def _to_sarif_result(self, match: MatchError) -> dict[str, Any]:
        # https://docs.oasis-open.org/sarif/sarif/v2.1.0/errata01/os/sarif-v2.1.0-errata01-os-complete.html#_Toc141790898
        if match.level not in ("warning", "error", "note", "none"):
            msg = "Unexpected failure to map '%s' level to SARIF."
            raise RuntimeError(
                msg,
                match.level,
            )

        result: dict[str, Any] = {
            "ruleId": match.tag,
            "level": self.get_sarif_result_severity_level(match),
            "message": {
                "text": (
                    str(match.details) if str(match.details) else str(match.message)
                ),
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": self._format_path(match.filename or ""),
                            "uriBaseId": self.BASE_URI_ID,
                        },
                        "region": {
                            "startLine": match.lineno,
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
    def get_sarif_rule_severity_level(rule: BaseRule) -> str:
        """General SARIF severity level for a rule.

        Note: Can differ from an actual result/match severity.
        Possible values: "none", "note", "warning", "error"

        see: https://github.com/oasis-tcs/sarif-spec/blob/123e95847b13fbdd4cbe2120fa5e33355d4a042b/Schemata/sarif-schema-2.1.0.json#L1934-L1939
        """
        if rule.severity in ["VERY_HIGH", "HIGH"]:
            return "error"

        if rule.severity in ["MEDIUM", "LOW", "VERY_LOW"]:
            return "warning"

        if rule.severity == "INFO":
            return "note"

        return "none"

    @staticmethod
    def get_sarif_result_severity_level(match: MatchError) -> str:
        """SARIF severity level for an actual result/match.

        Possible values: "none", "note", "warning", "error"

        see: https://github.com/oasis-tcs/sarif-spec/blob/123e95847b13fbdd4cbe2120fa5e33355d4a042b/Schemata/sarif-schema-2.1.0.json#L2066-L2071
        """
        if not match.level:
            return "none"

        if match.level in ["warning", "error"]:
            return match.level

        return "note"
