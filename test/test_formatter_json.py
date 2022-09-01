"""Test the codeclimate JSON formatter."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.formatters import CodeclimateJSONFormatter
from ansiblelint.rules import AnsibleLintRule


class TestCodeclimateJSONFormatter:
    """Unit test for CodeclimateJSONFormatter."""

    rule = AnsibleLintRule()
    matches: list[MatchError] = []
    formatter: CodeclimateJSONFormatter | None = None

    def setup_class(self) -> None:
        """Set up few MatchError objects."""
        self.rule = AnsibleLintRule()
        self.rule.id = "TCF0001"
        self.rule.severity = "VERY_HIGH"
        self.matches = []
        self.matches.append(
            MatchError(
                message="message",
                linenumber=1,
                details="hello",
                filename=Lintable("filename.yml"),
                rule=self.rule,
            )
        )
        self.matches.append(
            MatchError(
                message="message",
                linenumber=2,
                details="hello",
                filename=Lintable("filename.yml"),
                rule=self.rule,
            )
        )
        self.formatter = CodeclimateJSONFormatter(
            pathlib.Path.cwd(), display_relative_path=True
        )

    def test_format_list(self) -> None:
        """Test if the return value is a string."""
        assert isinstance(self.formatter, CodeclimateJSONFormatter)
        assert isinstance(self.formatter.format_result(self.matches), str)

    def test_result_is_json(self) -> None:
        """Test if returned string value is a JSON."""
        assert isinstance(self.formatter, CodeclimateJSONFormatter)
        json.loads(self.formatter.format_result(self.matches))

    def test_single_match(self) -> None:
        """Test negative case. Only lists are allowed. Otherwise a RuntimeError will be raised."""
        assert isinstance(self.formatter, CodeclimateJSONFormatter)
        with pytest.raises(RuntimeError):
            self.formatter.format_result(self.matches[0])  # type: ignore

    def test_result_is_list(self) -> None:
        """Test if the return JSON contains a list with a length of 2."""
        assert isinstance(self.formatter, CodeclimateJSONFormatter)
        result = json.loads(self.formatter.format_result(self.matches))
        assert len(result) == 2

    def test_validate_codeclimate_schema(self) -> None:
        """Test if the returned JSON is a valid codeclimate report."""
        assert isinstance(self.formatter, CodeclimateJSONFormatter)
        result = json.loads(self.formatter.format_result(self.matches))
        single_match = result[0]
        assert "type" in single_match
        assert single_match["type"] == "issue"
        assert "check_name" in single_match
        assert "categories" in single_match
        assert isinstance(single_match["categories"], list)
        assert "severity" in single_match
        assert single_match["severity"] == "blocker"
        assert "description" in single_match
        assert "fingerprint" in single_match
        assert "location" in single_match
        assert "path" in single_match["location"]
        assert single_match["location"]["path"] == self.matches[0].filename
        assert "lines" in single_match["location"]
        assert single_match["location"]["lines"]["begin"] == self.matches[0].linenumber


def test_code_climate_parsable_ignored() -> None:
    """Test that -p option does not alter codeclimate format."""
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
