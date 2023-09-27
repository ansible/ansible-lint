"""Tests for Transformer."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

import ansiblelint.__main__ as main
from ansiblelint.app import App

# noinspection PyProtectedMember
from ansiblelint.runner import LintResult, get_matches
from ansiblelint.transformer import Transformer

if TYPE_CHECKING:
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
    result = get_matches(rules=default_rules_collection, options=config_options)
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
        pytest.param(
            "examples/playbooks/transform-no-free-form.yml",
            2,
            True,
            id="no_free_form_transform",
        ),
        pytest.param(
            "examples/playbooks/transform-partial-become.yml",
            4,
            True,
            id="partial_become",
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


def test_pruned_err_after_fix(monkeypatch: pytest.MonkeyPatch, tmpdir: Path) -> None:
    """Test that pruned errors are not reported after fixing.

    :param monkeypatch: Monkeypatch
    :param tmpdir: Temporary directory
    """
    file = Path("examples/playbooks/transform-jinja.yml")
    source = Path.cwd() / file
    dest = tmpdir / source.name
    shutil.copyfile(source, dest)

    monkeypatch.setattr("sys.argv", ["ansible-lint", str(dest), "--fix=all"])

    fix_called = False
    orig_fix = main.fix

    def test_fix(
        runtime_options: Options,
        result: LintResult,
        rules: RulesCollection,
    ) -> None:
        """Wrap main.fix to check if it was called and match count is correct.

        :param runtime_options: Runtime options
        :param result: Lint result
        :param rules: Rules collection
        """
        nonlocal fix_called
        fix_called = True
        assert len(result.matches) == 7
        orig_fix(runtime_options, result, rules)

    report_called = False

    class TestApp(App):
        """Wrap App to check if it was called and match count is correct."""

        def report_outcome(
            self: TestApp,
            result: LintResult,
            *,
            mark_as_success: bool = False,
        ) -> int:
            """Wrap App.report_outcome to check if it was called and match count is correct.

            :param result: Lint result
            :param mark_as_success: Mark as success
            :returns: Exit code
            """
            nonlocal report_called
            report_called = True
            assert len(result.matches) == 1
            return super().report_outcome(result, mark_as_success=mark_as_success)

    monkeypatch.setattr("ansiblelint.__main__.fix", test_fix)
    monkeypatch.setattr("ansiblelint.app.App", TestApp)

    main.main()
    assert fix_called
    assert report_called
