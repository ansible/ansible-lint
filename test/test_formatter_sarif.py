"""Test the codeclimate JSON formatter."""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
from tempfile import NamedTemporaryFile

import pytest

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.formatters import SarifFormatter
from ansiblelint.rules import AnsibleLintRule, RulesCollection


class TestSarifFormatter:
    """Unit test for SarifFormatter."""

    rule1 = AnsibleLintRule()
    rule2 = AnsibleLintRule()
    matches: list[MatchError] = []
    formatter: SarifFormatter | None = None
    collection = RulesCollection()
    collection.register(rule1)
    collection.register(rule2)

    def setup_class(self) -> None:
        """Set up few MatchError objects."""
        self.rule1.id = "TCF0001"
        self.rule1.severity = "VERY_HIGH"
        self.rule1.description = "This is the rule description."
        self.rule1.link = "https://rules/help#TCF0001"
        self.rule1.tags = ["tag1", "tag2"]

        self.rule2.id = "TCF0002"
        self.rule2.severity = "MEDIUM"
        self.rule2.link = "https://rules/help#TCF0002"
        self.rule2.tags = ["tag3", "tag4"]

        self.matches.extend(
            [
                MatchError(
                    message="message1",
                    lineno=1,
                    column=10,
                    details="details1",
                    lintable=Lintable("filename1.yml", content=""),
                    rule=self.rule1,
                    tag="yaml[test1]",
                    ignored=False,
                ),
                MatchError(
                    message="message2",
                    lineno=2,
                    details="",
                    lintable=Lintable("filename2.yml", content=""),
                    rule=self.rule1,
                    tag="yaml[test2]",
                    ignored=True,
                ),
                MatchError(
                    message="message3",
                    lineno=666,
                    column=667,
                    details="details3",
                    lintable=Lintable("filename3.yml", content=""),
                    rule=self.rule2,
                    tag="yaml[test3]",
                    ignored=False,
                ),
            ],
        )

        self.formatter = SarifFormatter(pathlib.Path.cwd(), display_relative_path=True)

    def test_sarif_format_list(self) -> None:
        """Test if the return value is a string."""
        assert isinstance(self.formatter, SarifFormatter)
        assert isinstance(self.formatter.format_result(self.matches), str)

    def test_sarif_result_is_json(self) -> None:
        """Test if returned string value is a JSON."""
        assert isinstance(self.formatter, SarifFormatter)
        output = self.formatter.format_result(self.matches)
        json.loads(output)
        # https://github.com/ansible/ansible-navigator/issues/1490
        assert "\n" not in output

    def test_sarif_single_match(self) -> None:
        """Test negative case. Only lists are allowed. Otherwise, a RuntimeError will be raised."""
        assert isinstance(self.formatter, SarifFormatter)
        with pytest.raises(TypeError):
            self.formatter.format_result(self.matches[0])  # type: ignore[arg-type]

    def test_sarif_format(self) -> None:
        """Test if the return SARIF object contains the expected results."""
        assert isinstance(self.formatter, SarifFormatter)
        sarif = json.loads(self.formatter.format_result(self.matches))
        assert len(sarif["runs"][0]["results"]) == 3
        for result in sarif["runs"][0]["results"]:
            # Ensure all reported entries have a level
            assert "level" in result
            # Ensure reported levels are either error or warning
            assert result["level"] in ("error", "warning")

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
        assert len(rules) == 3
        assert rules[0]["id"] == self.matches[0].tag
        assert rules[0]["name"] == self.matches[0].tag
        assert rules[0]["shortDescription"]["text"] == self.matches[0].message
        assert rules[0]["defaultConfiguration"][
            "level"
        ] == SarifFormatter.get_sarif_rule_severity_level(self.matches[0].rule)
        assert rules[0]["help"]["text"] == self.matches[0].rule.description
        assert rules[0]["properties"]["tags"] == self.matches[0].rule.tags
        assert rules[0]["helpUri"] == self.matches[0].rule.url
        results = sarif["runs"][0]["results"]
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result["ruleId"] == self.matches[i].tag
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
                == self.matches[i].lineno
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
            assert result["level"] == SarifFormatter.get_sarif_result_severity_level(
                self.matches[i],
            )
        assert sarif["runs"][0]["originalUriBaseIds"][SarifFormatter.BASE_URI_ID]["uri"]
        assert results[0]["message"]["text"] == self.matches[0].details
        assert results[1]["message"]["text"] == self.matches[1].message


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


@pytest.mark.parametrize(
    ("file", "return_code"),
    (
        pytest.param("examples/playbooks/valid.yml", 0, id="0"),
        pytest.param("playbook.yml", 2, id="1"),
    ),
)
def test_sarif_file(file: str, return_code: int) -> None:
    """Test ability to dump sarif file (--sarif-file)."""
    with NamedTemporaryFile(mode="w", suffix=".sarif", prefix="output") as output_file:
        cmd = [
            sys.executable,
            "-m",
            "ansiblelint",
            "--sarif-file",
            str(output_file.name),
        ]
        result = subprocess.run([*cmd, file], check=False, capture_output=True)
        assert result.returncode == return_code
        assert os.path.exists(output_file.name)  # noqa: PTH110
        assert pathlib.Path(output_file.name).stat().st_size > 0


@pytest.mark.parametrize(
    ("file", "return_code"),
    (pytest.param("examples/playbooks/valid.yml", 0, id="0"),),
)
def test_sarif_file_creates_it_if_none_exists(file: str, return_code: int) -> None:
    """Test ability to create sarif file if none exists and dump output to it (--sarif-file)."""
    sarif_file_name = "test_output.sarif"
    cmd = [
        sys.executable,
        "-m",
        "ansiblelint",
        "--sarif-file",
        sarif_file_name,
    ]
    result = subprocess.run([*cmd, file], check=False, capture_output=True)
    assert result.returncode == return_code
    assert os.path.exists(sarif_file_name)  # noqa: PTH110
    assert pathlib.Path(sarif_file_name).stat().st_size > 0
    pathlib.Path.unlink(pathlib.Path(sarif_file_name))
