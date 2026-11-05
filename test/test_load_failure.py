"""Tests for LoadFailureRule."""

import json
import pathlib

import pytest

from ansiblelint.app import App
from ansiblelint.config import Options
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.formatters import CodeclimateJSONFormatter, PEP8Formatter
from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner


@pytest.mark.parametrize(
    "path",
    (
        pytest.param("examples/broken/encoding.j2", id="jinja2"),
        pytest.param("examples/broken/encoding.yml", id="yaml"),
    ),
)
def test_load_failure_encoding(
    path: str,
    default_rules_collection: RulesCollection,
) -> None:
    """Check that we fail when file encoding is wrong."""
    runner = Runner(path, rules=default_rules_collection)
    matches = runner.run()
    assert len(matches) == 1, matches
    assert matches[0].rule.id == "load-failure"
    assert "'utf-8' codec can't decode byte" in matches[0].message
    assert matches[0].tag == "load-failure[unicodedecodeerror]"


def test_load_failure_match_is_error_level(
    default_rules_collection: RulesCollection,
) -> None:
    """A load-failure match must be an error like the run summary counts it.

    Regression test for https://github.com/ansible/ansible-lint/issues/5226
    """
    runner = Runner(
        "examples/broken/encoding.yml",
        rules=default_rules_collection,
    )
    matches = runner.run()
    assert len(matches) == 1, matches
    assert matches[0].rule.id == "load-failure"
    assert matches[0].level == "error"

    formatter = CodeclimateJSONFormatter(
        pathlib.Path.cwd(),
        display_relative_path=True,
    )
    (issue,) = json.loads(formatter.format_result(matches))
    assert issue["severity"] == "major"

    # The same severity is already produced for loadable unskippable rules.
    syntax_match = MatchError(
        message="Couldn't resolve module/action 'totally_not_a_module'.",
        lintable=Lintable("playbook.yml", content=""),
        rule=default_rules_collection["syntax-check"],
        tag="syntax-check[unknown-module]",
    )
    assert syntax_match.level == "error"
    (issue,) = json.loads(formatter.format_result([syntax_match]))
    assert issue["severity"] == "major"


def test_internal_rule_levels_follow_warn_list(app: App) -> None:
    """Unloadable internal rules honor warn_list from their collection."""
    collection = RulesCollection(
        app=app,
        options=Options(warn_list=["internal-error", "experimental"]),
    )
    formatter = CodeclimateJSONFormatter(
        pathlib.Path.cwd(),
        display_relative_path=True,
    )
    pep8_formatter = PEP8Formatter(
        pathlib.Path.cwd(),
        display_relative_path=True,
    )
    for rule_id, level, severity in (
        ("load-failure", "error", "major"),
        ("parser-error", "error", "major"),
        ("internal-error", "warning", "minor"),
        ("warning", "warning", "minor"),
    ):
        match = MatchError(
            message="msg",
            lintable=Lintable("playbook.yml", content=""),
            rule=collection[rule_id],
        )
        assert match.level == level
        (issue,) = json.loads(formatter.format_result([match]))
        assert issue["severity"] == severity
        # PEP8 output keeps its "(warning)" suffix for warning-level matches
        # and drops it for errors.
        assert ("(warning)" in pep8_formatter.apply(match)) == (level == "warning")
