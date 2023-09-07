"""Tests for Transformer."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

# noinspection PyProtectedMember
from ansiblelint.runner import LintResult, _get_matches
from ansiblelint.transformer import Transformer

if TYPE_CHECKING:
    from pathlib import Path

    from ansiblelint.config import Options
    from ansiblelint.rules import RulesCollection


@pytest.fixture(name="runner_result")
def fixture_runner_result(
    config_options: Options,
    default_rules_collection: RulesCollection,
    playbook: str,
) -> LintResult:
    """Fixture that runs the Runner to populate a LintResult for a given file."""
    config_options.lintables = [playbook]
    result = _get_matches(rules=default_rules_collection, options=config_options)
    return result


@pytest.mark.parametrize(
    ("playbook", "matches_count", "transformed"),
    (
        # reuse TestRunner::test_runner test cases to ensure transformer does not mangle matches
        pytest.param(
            "examples/playbooks/nomatchestest.yml",
            0,
            False,
            id="nomatchestest",
        ),
        pytest.param("examples/playbooks/unicode.yml", 1, False, id="unicode"),
        pytest.param(
            "examples/playbooks/lots_of_warnings.yml",
            993,
            False,
            id="lots_of_warnings",
        ),
        pytest.param("examples/playbooks/become.yml", 0, False, id="become"),
        pytest.param(
            "examples/playbooks/contains_secrets.yml",
            0,
            False,
            id="contains_secrets",
        ),
        pytest.param(
            "examples/playbooks/vars/empty_vars.yml",
            0,
            False,
            id="empty_vars",
        ),
        pytest.param("examples/playbooks/vars/strings.yml", 0, True, id="strings"),
        pytest.param("examples/playbooks/vars/empty.yml", 1, False, id="empty"),
        pytest.param("examples/playbooks/name-case.yml", 1, True, id="name_case"),
        pytest.param("examples/playbooks/fqcn.yml", 3, True, id="fqcn"),
        pytest.param(
            "examples/playbooks/multi_yaml_doc.yml",
            1,
            False,
            id="multi_yaml_doc",
        ),
        pytest.param(
            "examples/playbooks/transform_command_instead_of_shell.yml",
            3,
            True,
            id="cmd_instead_of_shell",
        ),
        pytest.param(
            "examples/playbooks/transform-deprecated-local-action.yml",
            1,
            True,
            id="dep_local_action",
        ),
        pytest.param(
            "examples/playbooks/transform-block-indentation-indicator.yml",
            0,
            True,
            id="multiline_msg_with_indent_indicator",
        ),
        pytest.param(
            "examples/playbooks/transform-jinja.yml",
            7,
            True,
            id="jinja_spacing",
        ),
        pytest.param(
            "examples/playbooks/transform-no-jinja-when.yml",
            3,
            True,
            id="no_jinja_when",
        ),
        pytest.param(
            "examples/playbooks/vars/transform_nested_data.yml",
            3,
            True,
            id="nested",
        ),
        pytest.param(
            "examples/playbooks/transform-key-order.yml",
            6,
            True,
            id="key_order_transform",
        ),
    ),
)
def test_transformer(  # pylint: disable=too-many-arguments, too-many-locals
    config_options: Options,
    copy_examples_dir: tuple[Path, Path],
    playbook: str,
    runner_result: LintResult,
    transformed: bool,
    matches_count: int,
) -> None:
    """Test that transformer can go through any corner cases.

    Based on TestRunner::test_runner
    """
    config_options.write_list = ["all"]
    transformer = Transformer(result=runner_result, options=config_options)
    transformer.run()

    matches = runner_result.matches
    assert len(matches) == matches_count

    orig_dir, tmp_dir = copy_examples_dir
    orig_playbook = orig_dir / playbook
    expected_playbook = orig_dir / playbook.replace(".yml", ".transformed.yml")
    transformed_playbook = tmp_dir / playbook

    orig_playbook_content = orig_playbook.read_text()
    expected_playbook_content = expected_playbook.read_text()
    transformed_playbook_content = transformed_playbook.read_text()

    if transformed:
        assert orig_playbook_content != transformed_playbook_content
    else:
        assert orig_playbook_content == transformed_playbook_content

    assert transformed_playbook_content == expected_playbook_content


@pytest.mark.parametrize(
    ("write_list", "expected"),
    (
        # 1 item
        (["all"], {"all"}),
        (["none"], {"none"}),
        (["rule-id"], {"rule-id"}),
        # 2 items
        (["all", "all"], {"all"}),
        (["all", "none"], {"none"}),
        (["all", "rule-id"], {"all"}),
        (["none", "all"], {"all"}),
        (["none", "none"], {"none"}),
        (["none", "rule-id"], {"rule-id"}),
        (["rule-id", "all"], {"all"}),
        (["rule-id", "none"], {"none"}),
        (["rule-id", "rule-id"], {"rule-id"}),
        # 3 items
        (["all", "all", "all"], {"all"}),
        (["all", "all", "none"], {"none"}),
        (["all", "all", "rule-id"], {"all"}),
        (["all", "none", "all"], {"all"}),
        (["all", "none", "none"], {"none"}),
        (["all", "none", "rule-id"], {"rule-id"}),
        (["all", "rule-id", "all"], {"all"}),
        (["all", "rule-id", "none"], {"none"}),
        (["all", "rule-id", "rule-id"], {"all"}),
        (["none", "all", "all"], {"all"}),
        (["none", "all", "none"], {"none"}),
        (["none", "all", "rule-id"], {"all"}),
        (["none", "none", "all"], {"all"}),
        (["none", "none", "none"], {"none"}),
        (["none", "none", "rule-id"], {"rule-id"}),
        (["none", "rule-id", "all"], {"all"}),
        (["none", "rule-id", "none"], {"none"}),
        (["none", "rule-id", "rule-id"], {"rule-id"}),
        (["rule-id", "all", "all"], {"all"}),
        (["rule-id", "all", "none"], {"none"}),
        (["rule-id", "all", "rule-id"], {"all"}),
        (["rule-id", "none", "all"], {"all"}),
        (["rule-id", "none", "none"], {"none"}),
        (["rule-id", "none", "rule-id"], {"rule-id"}),
        (["rule-id", "rule-id", "all"], {"all"}),
        (["rule-id", "rule-id", "none"], {"none"}),
        (["rule-id", "rule-id", "rule-id"], {"rule-id"}),
    ),
)
def test_effective_write_set(write_list: list[str], expected: set[str]) -> None:
    """Make sure effective_write_set handles all/none keywords correctly."""
    actual = Transformer.effective_write_set(write_list)
    assert actual == expected
