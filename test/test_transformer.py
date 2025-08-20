# cspell:ignore classinfo
"""Tests for Transformer."""

from __future__ import annotations

import builtins
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest import mock
from unittest.mock import Mock

import pytest

import ansiblelint.__main__ as main
from ansiblelint.app import App
from ansiblelint.config import Options
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule, TransformMixin

# noinspection PyProtectedMember
from ansiblelint.runner import LintResult, get_matches
from ansiblelint.transformer import Transformer

if TYPE_CHECKING:
    from ansiblelint.rules import RulesCollection


@pytest.fixture(name="runner_result")
def fixture_runner_result(
    config_options: Options,
    default_rules_collection: RulesCollection,
    playbook_str: str,
    monkeypatch: pytest.MonkeyPatch,
) -> LintResult:
    """Fixture that runs the Runner to populate a LintResult for a given file."""
    # needed for testing transformer when roles/modules are missing:
    monkeypatch.setenv("ANSIBLE_LINT_NODEPS", "1")
    config_options.lintables = [playbook_str]
    result = get_matches(rules=default_rules_collection, options=config_options)
    return result


@pytest.mark.parametrize(
    ("playbook_str", "matches_count", "transformed", "is_owned_by_ansible"),
    (
        # reuse TestRunner::test_runner test cases to ensure transformer does not mangle matches
        pytest.param(
            "examples/playbooks/nomatchestest.yml",
            0,
            False,
            True,
            id="nomatchestest",
        ),
        pytest.param("examples/playbooks/unicode.yml", 1, False, True, id="unicode"),
        pytest.param(
            "examples/playbooks/lots_of_warnings.yml",
            993,
            False,
            True,
            id="lots_of_warnings",
        ),
        pytest.param("examples/playbooks/become.yml", 0, False, True, id="become"),
        pytest.param(
            "examples/playbooks/contains_secrets.yml",
            0,
            False,
            True,
            id="contains_secrets",
        ),
        pytest.param(
            "examples/playbooks/vars/empty_vars.yml",
            0,
            False,
            True,
            id="empty_vars",
        ),
        pytest.param(
            "examples/playbooks/vars/strings.yml",
            0,
            True,
            True,
            id="strings",
        ),
        pytest.param("examples/playbooks/vars/empty.yml", 1, False, True, id="empty"),
        pytest.param("examples/playbooks/fqcn.yml", 3, True, True, id="fqcn"),
        pytest.param(
            "examples/playbooks/multi_yaml_doc.yml",
            1,
            False,
            True,
            id="multi_yaml_doc",
        ),
        pytest.param(
            "examples/playbooks/transform_command_instead_of_shell.yml",
            3,
            True,
            True,
            id="cmd_instead_of_shell",
        ),
        pytest.param(
            "examples/playbooks/transform-deprecated-local-action.yml",
            1,
            True,
            True,
            id="dep_local_action",
        ),
        pytest.param(
            "examples/playbooks/transform-block-indentation-indicator.yml",
            0,
            True,
            True,
            id="multiline_msg_with_indent_indicator",
        ),
        pytest.param(
            "examples/playbooks/transform-jinja.yml",
            7,
            True,
            True,
            id="jinja_spacing",
        ),
        pytest.param(
            "examples/playbooks/transform-no-jinja-when.yml",
            3,
            True,
            True,
            id="no_jinja_when",
        ),
        pytest.param(
            "examples/playbooks/vars/transform_nested_data.yml",
            3,
            True,
            True,
            id="nested",
        ),
        pytest.param(
            "examples/playbooks/transform-key-order.yml",
            6,
            True,
            True,
            id="key_order_transform",
        ),
        pytest.param(
            "examples/playbooks/transform-no-free-form.yml",
            5,
            True,
            True,
            id="no_free_form_transform",
        ),
        pytest.param(
            "examples/playbooks/transform-partial-become.yml",
            4,
            True,
            True,
            id="partial_become",
        ),
        pytest.param(
            "examples/playbooks/transform-key-order-play.yml",
            1,
            True,
            True,
            id="key_order_play_transform",
        ),
        pytest.param(
            "examples/playbooks/transform-key-order-block.yml",
            1,
            True,
            True,
            id="key_order_block_transform",
        ),
        pytest.param(
            "examples/.github/workflows/sample.yml",
            0,
            False,
            False,
            id="github-workflow",
        ),
        pytest.param(
            "examples/playbooks/invalid-transform.yml",
            1,
            False,
            True,
            id="invalid_transform",
        ),
        pytest.param(
            "examples/roles/name_prefix/tasks/test.yml",
            1,
            True,
            True,
            id="name_casing_prefix",
        ),
        pytest.param(
            "examples/roles/name_casing/tasks/main.yml",
            2,
            True,
            True,
            id="name_case_roles",
        ),
        pytest.param(
            "examples/playbooks/4114/transform-with-missing-role-and-modules.yml",
            1,
            True,
            True,
            id="4114",
        ),
        pytest.param(
            "examples/playbooks/transform-name.yml",
            3,
            True,
            True,
            id="name-capitalize",
        ),
    ),
)
@mock.patch.dict(os.environ, {"ANSIBLE_LINT_WRITE_TMP": "1"}, clear=True)
@pytest.mark.libyaml
def test_transformer(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    config_options: Options,
    playbook_str: str,
    runner_result: LintResult,
    transformed: bool,
    is_owned_by_ansible: bool,
    matches_count: int,
) -> None:
    """Test that transformer can go through any corner cases.

    Based on TestRunner::test_runner
    """
    # test ability to detect is_owned_by_ansible
    assert Lintable(playbook_str).is_owned_by_ansible() == is_owned_by_ansible
    playbook = Path(playbook_str)
    config_options.write_list = ["all"]

    matches = runner_result.matches
    assert len(matches) == matches_count

    transformer = Transformer(result=runner_result, options=config_options)
    transformer.run()

    orig_content = playbook.read_text(encoding="utf-8")
    if transformed:
        expected_content = playbook.with_suffix(
            f".transformed{playbook.suffix}",
        ).read_text(encoding="utf-8")
        transformed_content = playbook.with_suffix(f".tmp{playbook.suffix}").read_text(
            encoding="utf-8",
        )

        assert orig_content != transformed_content
        assert expected_content == transformed_content
        playbook.with_suffix(f".tmp{playbook.suffix}").unlink()


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


@pytest.mark.parametrize(
    ("write_list", "write_exclude_list", "rules"),
    (
        (
            ["all"],
            ["none"],
            [("rule-id", True), ("rule1", True), ("rule-03", True)],
        ),
        (
            ["all"],
            ["all"],
            [("rule-id", False), ("rule1", False), ("rule-03", False)],
        ),
        (
            ["none"],
            ["none"],
            [("rule-id", False), ("rule1", False), ("rule-03", False)],
        ),
        (
            ["none"],
            ["all"],
            [("rule-id", False), ("rule1", False), ("rule-03", False)],
        ),
        (
            ["rule-id"],
            ["none"],
            [("rule-id", True), ("rule1", False), ("rule-03", False)],
        ),
        (
            ["rule-id"],
            ["all"],
            [("rule-id", False), ("rule1", False), ("rule-03", False)],
        ),
    ),
)
def test_write_exclude_list(
    write_list: list[str],
    write_exclude_list: list[str],
    rules: list[tuple[str, bool]],
) -> None:
    """Test item matching write_exclude_list are excluded correctly."""
    matches: list[MatchError] = []

    class TestRule(AnsibleLintRule, TransformMixin):
        """Dummy class for transformable rules."""

    for rule_id, transform_expected in rules:
        rule = Mock(spec=TestRule)
        rule.id = rule_id
        rule.tags = []
        rule.transform_expected = transform_expected
        match = MatchError(rule=rule)
        matches.append(match)

    transformer = Transformer(
        LintResult(matches, set()),
        Options(write_list=write_list, write_exclude_list=write_exclude_list),
    )
    # noinspection PyTypeChecker
    Transformer._do_transforms(transformer, Mock(), "", False, matches)  # noqa: SLF001

    for match in matches:
        if match.rule.transform_expected:  # type: ignore[attr-defined]
            match.rule.transform.assert_called()  # type: ignore[attr-defined]
        else:
            match.rule.transform.assert_not_called()  # type: ignore[attr-defined]


@pytest.mark.libyaml
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
    # disable the App() caching because we cannot prevent the initial initialization from happening
    monkeypatch.setattr("ansiblelint.app._CACHED_APP", None)

    main.main()
    assert fix_called
    assert report_called


class TransformTests:
    """A carrier for some common test constants."""

    FILE_NAME = "examples/playbooks/transform-no-free-form.yml"
    FILE_TYPE = "playbook"
    LINENO = 5
    ID = "no-free-form"
    MATCH_TYPE = "task"
    VERSION_PART = "version=(1, 1)"

    @classmethod
    def match_id(cls) -> str:
        """Generate a match id.

        :returns: Match id string
        """
        return f"{cls.ID}/{cls.MATCH_TYPE} {cls.FILE_NAME}:{cls.LINENO}"

    @classmethod
    def rewrite_part(cls) -> str:
        """Generate a rewrite part.

        :returns: Rewrite part string
        """
        return f"{cls.FILE_NAME} ({cls.FILE_TYPE}), {cls.VERSION_PART}"


@pytest.fixture(name="test_result")
def fixture_test_result(
    config_options: Options,
    default_rules_collection: RulesCollection,
) -> tuple[LintResult, Options]:
    """Fixture that runs the Runner to populate a LintResult for a given file.

    The results are confirmed and a limited to a single match.

    :param config_options: Configuration options
    :param default_rules_collection: Default rules collection
    :returns: Tuple of LintResult and Options
    """
    config_options.write_list = [TransformTests.ID]
    config_options.lintables = [TransformTests.FILE_NAME]

    result = get_matches(rules=default_rules_collection, options=config_options)
    match = result.matches[0]

    def write(*_args: Any, **_kwargs: Any) -> None:
        """Don't rewrite the test fixture.

        :param _args: Arguments
        :param _kwargs: Keyword arguments
        """

    setattr(match.lintable, "write", write)  # noqa: B010

    assert match.rule.id == TransformTests.ID
    assert match.filename == TransformTests.FILE_NAME
    assert match.lineno == TransformTests.LINENO
    assert match.match_type == TransformTests.MATCH_TYPE
    result.matches = [match]

    return result, config_options


@pytest.mark.libyaml
def test_transform_na(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    test_result: tuple[LintResult, Options],
) -> None:
    """Test the transformer is not available.

    :param caplog: Log capture fixture
    :param monkeypatch: Monkeypatch
    :param test_result: Test result fixture
    """
    result = test_result[0]
    options = test_result[1]

    isinstance_ = builtins.isinstance
    called = False

    def mp_isinstance(t_object: Any, classinfo: type) -> bool:
        if classinfo is TransformMixin:
            nonlocal called
            called = True
            return False
        return isinstance_(t_object, classinfo)

    monkeypatch.setattr(builtins, "isinstance", mp_isinstance)

    transformer = Transformer(result=result, options=options)
    with caplog.at_level(10):
        transformer.run()

    assert called
    logs = [record for record in caplog.records if record.module == "transformer"]
    assert len(logs) == 2

    log_0 = f"{transformer.FIX_NA_MSG} {TransformTests.match_id()}"
    assert logs[0].message == log_0
    assert logs[0].levelname == "DEBUG"

    log_1 = f"{transformer.DUMP_MSG} {TransformTests.rewrite_part()}"
    assert logs[1].message == log_1
    assert logs[1].levelname == "DEBUG"


@pytest.mark.libyaml
def test_transform_no_tb(
    caplog: pytest.LogCaptureFixture,
    test_result: tuple[LintResult, Options],
) -> None:
    """Test the transformer does not traceback.

    :param caplog: Log capture fixture
    :param test_result: Test result fixture
    :raises RuntimeError: If the rule is not a TransformMixin
    """
    result = test_result[0]
    options = test_result[1]
    exception_msg = "FixFailure"

    def transform(*_args: Any, **_kwargs: Any) -> None:
        """Raise an exception for the transform call.

        :raises RuntimeError: Always
        """
        raise RuntimeError(exception_msg)

    if isinstance(result.matches[0].rule, TransformMixin):
        setattr(result.matches[0].rule, "transform", transform)  # noqa: B010
    else:
        err = "Rule is not a TransformMixin"
        raise TypeError(err)

    transformer = Transformer(result=result, options=options)
    with caplog.at_level(10):
        transformer.run()

    logs = [record for record in caplog.records if record.module == "transformer"]
    assert len(logs) == 5

    log_0 = f"{transformer.FIX_APPLY_MSG} {TransformTests.match_id()}"
    assert logs[0].message == log_0
    assert logs[0].levelname == "DEBUG"

    log_1 = f"{transformer.FIX_FAILED_MSG} {TransformTests.match_id()}"
    assert logs[1].message == log_1
    assert logs[1].levelname == "ERROR"

    log_2 = exception_msg
    assert logs[2].message == log_2
    assert logs[2].levelname == "ERROR"

    log_3 = f"{transformer.FIX_ISSUE_MSG}"
    assert logs[3].message == log_3
    assert logs[3].levelname == "ERROR"

    log_4 = f"{transformer.DUMP_MSG} {TransformTests.rewrite_part()}"
    assert logs[4].message == log_4
    assert logs[4].levelname == "DEBUG"


@pytest.mark.libyaml
def test_transform_applied(
    caplog: pytest.LogCaptureFixture,
    test_result: tuple[LintResult, Options],
) -> None:
    """Test the transformer is applied.

    :param caplog: Log capture fixture
    :param test_result: Test result fixture
    """
    result = test_result[0]
    options = test_result[1]

    transformer = Transformer(result=result, options=options)
    with caplog.at_level(10):
        transformer.run()

    logs = [record for record in caplog.records if record.module == "transformer"]
    assert len(logs) == 3

    log_0 = f"{transformer.FIX_APPLY_MSG} {TransformTests.match_id()}"
    assert logs[0].message == log_0
    assert logs[0].levelname == "DEBUG"

    log_1 = f"{transformer.FIX_APPLIED_MSG} {TransformTests.match_id()}"
    assert logs[1].message == log_1
    assert logs[1].levelname == "DEBUG"

    log_2 = f"{transformer.DUMP_MSG} {TransformTests.rewrite_part()}"
    assert logs[2].message == log_2
    assert logs[2].levelname == "DEBUG"


@pytest.mark.libyaml
def test_transform_not_enabled(
    caplog: pytest.LogCaptureFixture,
    test_result: tuple[LintResult, Options],
) -> None:
    """Test the transformer is not enabled.

    :param caplog: Log capture fixture
    :param test_result: Test result fixture
    """
    result = test_result[0]
    options = test_result[1]
    options.write_list = []

    transformer = Transformer(result=result, options=options)
    with caplog.at_level(10):
        transformer.run()

    logs = [record for record in caplog.records if record.module == "transformer"]
    assert len(logs) == 2

    log_0 = f"{transformer.FIX_NE_MSG} {TransformTests.match_id()}"
    assert logs[0].message == log_0
    assert logs[0].levelname == "DEBUG"

    log_1 = f"{transformer.DUMP_MSG} {TransformTests.rewrite_part()}"
    assert logs[1].message == log_1
    assert logs[1].levelname == "DEBUG"


@pytest.mark.libyaml
def test_transform_not_applied(
    caplog: pytest.LogCaptureFixture,
    test_result: tuple[LintResult, Options],
) -> None:
    """Test the transformer is not applied.

    :param caplog: Log capture fixture
    :param test_result: Test result fixture
    :raises RuntimeError: If the rule is not a TransformMixin
    """
    result = test_result[0]
    options = test_result[1]

    called = False

    def transform(match: MatchError, *_args: Any, **_kwargs: Any) -> None:
        """Do not apply the transform.

        :param match: Match object
        :param _args: Arguments
        :param _kwargs: Keyword arguments
        """
        nonlocal called
        called = True
        match.fixed = False

    if isinstance(result.matches[0].rule, TransformMixin):
        setattr(result.matches[0].rule, "transform", transform)  # noqa: B010
    else:
        err = "Rule is not a TransformMixin"
        raise TypeError(err)

    transformer = Transformer(result=result, options=options)
    with caplog.at_level(10):
        transformer.run()

    assert called
    logs = [record for record in caplog.records if record.module == "transformer"]
    assert len(logs) == 3

    log_0 = f"{transformer.FIX_APPLY_MSG} {TransformTests.match_id()}"
    assert logs[0].message == log_0
    assert logs[0].levelname == "DEBUG"

    log_1 = f"{transformer.FIX_NOT_APPLIED_MSG} {TransformTests.match_id()}"
    assert logs[1].message == log_1
    assert logs[1].levelname == "ERROR"

    log_2 = f"{transformer.DUMP_MSG} {TransformTests.rewrite_part()}"
    assert logs[2].message == log_2
    assert logs[2].levelname == "DEBUG"
