"""Test the codeclimate JSON formatter."""

from __future__ import annotations

import json
import pathlib

import pytest

from ansiblelint.app import App  # noqa: TC001
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.formatters import CodeclimateJSONFormatter
from ansiblelint.rules import AnsibleLintRule, RulesCollection

# pylint: disable=redefined-outer-name


@pytest.fixture
def json_formatter_rule() -> AnsibleLintRule:
    """Create a test rule for JSON formatter tests."""
    rule = AnsibleLintRule()
    rule.id = "TCF0001"
    rule.severity = "VERY_HIGH"
    return rule


@pytest.fixture
def json_formatter_collection(
    json_formatter_rule: AnsibleLintRule,
    app: App,
) -> RulesCollection:
    """Create a rules collection with the test rule."""
    collection = RulesCollection(app=app)
    collection.register(json_formatter_rule)
    return collection


@pytest.fixture
def json_formatter_matches(
    json_formatter_collection: RulesCollection,  # noqa: ARG001
    json_formatter_rule: AnsibleLintRule,
) -> list[MatchError]:
    """Create test match errors for JSON formatter tests."""
    # Ensure rule is registered in collection (which sets _collection on the rule)
    # This is needed so that match.level returns "error" instead of "warning"
    # The collection fixture ensures the rule is registered before we create MatchError
    return [
        MatchError(
            message="message",
            lineno=1,
            details="hello",
            lintable=Lintable("filename.yml", content=""),
            rule=json_formatter_rule,
        ),
        MatchError(
            message="message",
            lineno=2,
            details="hello",
            lintable=Lintable("filename.yml", content=""),
            rule=json_formatter_rule,
            ignored=True,
        ),
    ]


@pytest.fixture
def json_formatter() -> CodeclimateJSONFormatter:
    """Create a CodeclimateJSONFormatter instance."""
    return CodeclimateJSONFormatter(
        pathlib.Path.cwd(),
        display_relative_path=True,
    )


def test_json_format_list(
    json_formatter: CodeclimateJSONFormatter,
    json_formatter_matches: list[MatchError],
) -> None:
    """Test if the return value is a string."""
    assert isinstance(json_formatter, CodeclimateJSONFormatter)
    assert isinstance(json_formatter.format_result(json_formatter_matches), str)


def test_result_is_json(
    json_formatter: CodeclimateJSONFormatter,
    json_formatter_matches: list[MatchError],
) -> None:
    """Test if returned string value is a JSON."""
    assert isinstance(json_formatter, CodeclimateJSONFormatter)
    output = json_formatter.format_result(json_formatter_matches)
    json.loads(output)
    # https://github.com/ansible/ansible-navigator/issues/1490
    assert "\n" not in output


def test_json_single_match(
    json_formatter: CodeclimateJSONFormatter,
    json_formatter_matches: list[MatchError],
) -> None:
    """Test negative case. Only lists are allowed. Otherwise a RuntimeError will be raised."""
    assert isinstance(json_formatter, CodeclimateJSONFormatter)
    with pytest.raises(TypeError):
        json_formatter.format_result(json_formatter_matches[0])  # type: ignore[arg-type]


def test_result_is_list(
    json_formatter: CodeclimateJSONFormatter,
    json_formatter_matches: list[MatchError],
) -> None:
    """Test if the return JSON contains a list with a length of 2."""
    assert isinstance(json_formatter, CodeclimateJSONFormatter)
    result = json.loads(json_formatter.format_result(json_formatter_matches))
    assert len(result) == 2


def test_validate_codeclimate_schema(
    json_formatter: CodeclimateJSONFormatter,
    json_formatter_matches: list[MatchError],
) -> None:
    """Test if the returned JSON is a valid codeclimate report."""
    assert isinstance(json_formatter, CodeclimateJSONFormatter)
    result = json.loads(json_formatter.format_result(json_formatter_matches))
    single_match = result[0]
    assert "type" in single_match
    assert single_match["type"] == "issue"
    assert "check_name" in single_match
    assert "categories" in single_match
    assert isinstance(single_match["categories"], list)
    assert "severity" in single_match
    assert single_match["severity"] == "major"
    assert "description" in single_match
    assert "fingerprint" in single_match
    assert "location" in single_match
    assert "path" in single_match["location"]
    assert single_match["location"]["path"] == json_formatter_matches[0].filename
    assert "lines" in single_match["location"]
    assert (
        single_match["location"]["lines"]["begin"] == json_formatter_matches[0].lineno
    )
    assert "positions" not in single_match["location"]
    # check that the 2nd match is marked as 'minor' because it was created with ignored=True
    assert result[1]["severity"] == "minor"


def test_validate_codeclimate_schema_with_positions(
    json_formatter: CodeclimateJSONFormatter,
    json_formatter_collection: RulesCollection,  # noqa: ARG001
    json_formatter_rule: AnsibleLintRule,
) -> None:
    """Test if the returned JSON is a valid codeclimate report (containing 'positions' instead of 'lines')."""
    # The collection fixture ensures the rule is registered before we create MatchError
    assert isinstance(json_formatter, CodeclimateJSONFormatter)
    result = json.loads(
        json_formatter.format_result(
            [
                MatchError(
                    message="message",
                    lineno=1,
                    column=42,
                    details="hello",
                    lintable=Lintable("filename.yml", content=""),
                    rule=json_formatter_rule,
                ),
            ],
        ),
    )
    assert result[0]["location"]["positions"]["begin"]["line"] == 1
    assert result[0]["location"]["positions"]["begin"]["column"] == 42
    assert "lines" not in result[0]["location"]
