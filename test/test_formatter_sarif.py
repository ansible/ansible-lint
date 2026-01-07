"""Test the codeclimate JSON formatter."""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
from tempfile import NamedTemporaryFile

import pytest

from ansiblelint.app import App  # noqa: TC001
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.formatters import SarifFormatter
from ansiblelint.rules import AnsibleLintRule, RulesCollection

# pylint: disable=redefined-outer-name


@pytest.fixture
def sarif_formatter_rule1() -> AnsibleLintRule:
    """Create first test rule for SARIF formatter tests."""
    rule = AnsibleLintRule()
    rule.id = "TCF0001"
    rule.severity = "VERY_HIGH"
    rule.description = "This is the rule description."
    rule.link = "https://rules/help#TCF0001"
    rule.tags = ["tag1", "tag2"]
    return rule


@pytest.fixture
def sarif_formatter_rule2() -> AnsibleLintRule:
    """Create second test rule for SARIF formatter tests."""
    rule = AnsibleLintRule()
    rule.id = "TCF0002"
    rule.severity = "MEDIUM"
    rule.link = "https://rules/help#TCF0002"
    rule.tags = ["tag3", "tag4"]
    return rule


@pytest.fixture
def sarif_formatter_collection(
    sarif_formatter_rule1: AnsibleLintRule,
    sarif_formatter_rule2: AnsibleLintRule,
    app: App,
) -> RulesCollection:
    """Create a rules collection with the test rules."""
    collection = RulesCollection(app=app)
    collection.register(sarif_formatter_rule1)
    collection.register(sarif_formatter_rule2)
    return collection


@pytest.fixture
def sarif_formatter_matches(
    sarif_formatter_rule1: AnsibleLintRule,
    sarif_formatter_rule2: AnsibleLintRule,
) -> list[MatchError]:
    """Create test match errors for SARIF formatter tests."""
    return [
        MatchError(
            message="message1",
            lineno=1,
            column=10,
            details="details1",
            lintable=Lintable("filename1.yml", content=""),
            rule=sarif_formatter_rule1,
            tag="yaml[test1]",
            ignored=False,
        ),
        MatchError(
            message="message2",
            lineno=2,
            details="",
            lintable=Lintable("filename2.yml", content=""),
            rule=sarif_formatter_rule1,
            tag="yaml[test2]",
            ignored=True,
        ),
        MatchError(
            message="message3",
            lineno=666,
            column=667,
            details="details3",
            lintable=Lintable("filename3.yml", content=""),
            rule=sarif_formatter_rule2,
            tag="yaml[test3]",
            ignored=False,
        ),
    ]


@pytest.fixture
def sarif_formatter() -> SarifFormatter:
    """Create a SarifFormatter instance."""
    return SarifFormatter(pathlib.Path.cwd(), display_relative_path=True)


def test_sarif_format_list(
    sarif_formatter: SarifFormatter,
    sarif_formatter_matches: list[MatchError],
) -> None:
    """Test if the return value is a string."""
    assert isinstance(sarif_formatter, SarifFormatter)
    assert isinstance(sarif_formatter.format_result(sarif_formatter_matches), str)


def test_sarif_result_is_json(
    sarif_formatter: SarifFormatter,
    sarif_formatter_matches: list[MatchError],
) -> None:
    """Test if returned string value is a JSON."""
    assert isinstance(sarif_formatter, SarifFormatter)
    output = sarif_formatter.format_result(sarif_formatter_matches)
    json.loads(output)
    # https://github.com/ansible/ansible-navigator/issues/1490
    assert "\n" not in output


def test_sarif_single_match(
    sarif_formatter: SarifFormatter,
    sarif_formatter_matches: list[MatchError],
) -> None:
    """Test negative case. Only lists are allowed. Otherwise, a RuntimeError will be raised."""
    assert isinstance(sarif_formatter, SarifFormatter)
    with pytest.raises(TypeError):
        sarif_formatter.format_result(sarif_formatter_matches[0])  # type: ignore[arg-type]


def test_sarif_format(
    sarif_formatter: SarifFormatter,
    sarif_formatter_matches: list[MatchError],
) -> None:
    """Test if the return SARIF object contains the expected results."""
    assert isinstance(sarif_formatter, SarifFormatter)
    sarif = json.loads(sarif_formatter.format_result(sarif_formatter_matches))
    assert len(sarif["runs"][0]["results"]) == 3
    for result in sarif["runs"][0]["results"]:
        # Ensure all reported entries have a level
        assert "level" in result
        # Ensure reported levels are either error or warning
        assert result["level"] in ("error", "warning")


def test_validate_sarif_schema(
    sarif_formatter: SarifFormatter,
    sarif_formatter_matches: list[MatchError],
) -> None:
    """Test if the returned JSON is a valid SARIF report."""
    assert isinstance(sarif_formatter, SarifFormatter)
    sarif = json.loads(sarif_formatter.format_result(sarif_formatter_matches))
    assert sarif["$schema"] == SarifFormatter.SARIF_SCHEMA
    assert sarif["version"] == SarifFormatter.SARIF_SCHEMA_VERSION
    driver = sarif["runs"][0]["tool"]["driver"]
    assert driver["name"] == SarifFormatter.TOOL_NAME
    assert driver["informationUri"] == SarifFormatter.TOOL_URL
    rules = driver["rules"]
    assert len(rules) == 3
    assert rules[0]["id"] == sarif_formatter_matches[0].tag
    assert rules[0]["name"] == sarif_formatter_matches[0].tag
    assert rules[0]["shortDescription"]["text"] == sarif_formatter_matches[0].message
    assert rules[0]["defaultConfiguration"][
        "level"
    ] == SarifFormatter.get_sarif_rule_severity_level(sarif_formatter_matches[0].rule)
    assert rules[0]["help"]["text"] == sarif_formatter_matches[0].rule.description
    assert rules[0]["properties"]["tags"] == sarif_formatter_matches[0].rule.tags
    assert rules[0]["helpUri"] == sarif_formatter_matches[0].rule.url
    results = sarif["runs"][0]["results"]
    assert len(results) == 3
    for i, result in enumerate(results):
        assert result["ruleId"] == sarif_formatter_matches[i].tag
        assert (
            result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
            == sarif_formatter_matches[i].filename
        )
        assert (
            result["locations"][0]["physicalLocation"]["artifactLocation"]["uriBaseId"]
            == SarifFormatter.BASE_URI_ID
        )
        assert (
            result["locations"][0]["physicalLocation"]["region"]["startLine"]
            == sarif_formatter_matches[i].lineno
        )
        if sarif_formatter_matches[i].column:
            assert (
                result["locations"][0]["physicalLocation"]["region"]["startColumn"]
                == sarif_formatter_matches[i].column
            )
        else:
            assert (
                "startColumn"
                not in result["locations"][0]["physicalLocation"]["region"]
            )
        assert result["level"] == SarifFormatter.get_sarif_result_severity_level(
            sarif_formatter_matches[i],
        )
    assert sarif["runs"][0]["originalUriBaseIds"][SarifFormatter.BASE_URI_ID]["uri"]
    assert results[0]["message"]["text"] == sarif_formatter_matches[0].details
    assert results[1]["message"]["text"] == sarif_formatter_matches[1].message


@pytest.mark.parametrize(
    ("file", "return_code"),
    (
        pytest.param("examples/playbooks/valid.yml", 0, id="0"),
        pytest.param("playbook.yml", 2, id="1"),
    ),
)
def test_sarif_file(file: str, return_code: int) -> None:
    """Test ability to dump sarif file (--sarif-file)."""
    with NamedTemporaryFile(
        mode="w", suffix=".sarif", prefix="output", encoding="utf-8"
    ) as output_file:
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
