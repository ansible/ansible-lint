"""Test the codeclimate JSON formatter."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.formatters import SarifFormatter
from ansiblelint.rules import AnsibleLintRule


class TestSarifFormatter:
    """Unit test for SarifFormatter."""

    rule = AnsibleLintRule()
    matches: list[MatchError] = []
    formatter: SarifFormatter | None = None

    def setup_class(self) -> None:
        """Set up few MatchError objects."""
        self.rule = AnsibleLintRule()
        self.rule.id = "TCF0001"
        self.rule.severity = "VERY_HIGH"
        self.rule.description = "This is the rule description."
        self.rule.link = "https://rules/help#TCF0001"
        self.rule.tags = ["tag1", "tag2"]
        self.matches = []
        self.matches.append(
            MatchError(
                message="message",
                linenumber=1,
                column=10,
                details="hello",
                filename=Lintable("filename.yml"),
                rule=self.rule,
                tag="yaml[test]",
            )
        )
        self.matches.append(
            MatchError(
                message="message",
                linenumber=2,
                details="hello",
                filename=Lintable("filename.yml"),
                rule=self.rule,
                tag="yaml[test]",
            )
        )
        self.formatter = SarifFormatter(pathlib.Path.cwd(), display_relative_path=True)

    def test_format_list(self) -> None:
        """Test if the return value is a string."""
        assert isinstance(self.formatter, SarifFormatter)
        assert isinstance(self.formatter.format_result(self.matches), str)

    def test_result_is_json(self) -> None:
        """Test if returned string value is a JSON."""
        assert isinstance(self.formatter, SarifFormatter)
        json.loads(self.formatter.format_result(self.matches))

    def test_single_match(self) -> None:
        """Test negative case. Only lists are allowed. Otherwise a RuntimeError will be raised."""
        assert isinstance(self.formatter, SarifFormatter)
        with pytest.raises(RuntimeError):
            self.formatter.format_result(self.matches[0])  # type: ignore

    def test_result_is_list(self) -> None:
        """Test if the return SARIF object contains the results with length of 2."""
        assert isinstance(self.formatter, SarifFormatter)
        sarif = json.loads(self.formatter.format_result(self.matches))
        assert len(sarif["runs"][0]["results"]) == 2

    def test_validate_sarif_schema(self) -> None:
        """Test if the returned JSON is a valid SARIF report."""
        assert isinstance(self.formatter, SarifFormatter)
        sarif = json.loads(self.formatter.format_result(self.matches))
        assert sarif["$schema"] == SarifFormatter.SARIF_SCHEMA
        assert sarif["version"] == SarifFormatter.SARIF_SCHEMA_VERSION
        driver = sarif["runs"][0]["tool"]["driver"]
        assert driver["name"] == SarifFormatter.TOOL_NAME
        assert driver["informationUri"] == SarifFormatter.TOOL_URL
        rules = driver["rules"]
        assert len(rules) == 1
        assert rules[0]["id"] == self.matches[0].tag
        assert rules[0]["name"] == self.matches[0].tag
        assert rules[0]["shortDescription"]["text"] == self.matches[0].message
        assert rules[0]["defaultConfiguration"]["level"] == "error"
        assert rules[0]["help"]["text"] == self.matches[0].rule.description
        assert rules[0]["properties"]["tags"] == self.matches[0].rule.tags
        assert rules[0]["helpUri"] == self.rule.link
        results = sarif["runs"][0]["results"]
        assert len(results) == 2
        for i, result in enumerate(results):
            assert result["ruleId"] == self.matches[i].tag
            assert result["message"]["text"] == self.matches[0].message
            assert (
                result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
                == self.matches[i].filename
            )
            assert (
                result["locations"][0]["physicalLocation"]["artifactLocation"][
                    "uriBaseId"
                ]
                == SarifFormatter.BASE_URI_ID
            )
            assert (
                result["locations"][0]["physicalLocation"]["region"]["startLine"]
                == self.matches[i].linenumber
            )
            if self.matches[i].column:
                assert (
                    result["locations"][0]["physicalLocation"]["region"]["startColumn"]
                    == self.matches[i].column
                )
            else:
                assert (
                    "startColumn"
                    not in result["locations"][0]["physicalLocation"]["region"]
                )
        assert sarif["runs"][0]["originalUriBaseIds"][SarifFormatter.BASE_URI_ID]["uri"]


def test_sarif_parsable_ignored() -> None:
    """Test that -p option does not alter SARIF format."""
    cmd = [
        sys.executable,
        "-m",
        "ansiblelint",
        "-v",
        "-p",
    ]
    file = "examples/playbooks/empty_playbook.yml"
    result = subprocess.run([*cmd, file], check=False)
    result2 = subprocess.run([*cmd, "-p", file], check=False)

    assert result.returncode == result2.returncode
    assert result.stdout == result2.stdout
