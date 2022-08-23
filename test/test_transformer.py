"""Tests for Transformer."""
from __future__ import annotations

import os
import pathlib
import shutil
from argparse import Namespace
from typing import Iterator

import pytest

from ansiblelint.rules import RulesCollection

# noinspection PyProtectedMember
from ansiblelint.runner import LintResult, _get_matches
from ansiblelint.transformer import Transformer


@pytest.fixture(name="copy_examples_dir")
def fixture_copy_examples_dir(
    tmp_path: pathlib.Path, config_options: Namespace
) -> Iterator[tuple[pathlib.Path, pathlib.Path]]:
    """Fixture that copies the examples/ dir into a tmpdir."""
    examples_dir = pathlib.Path("examples")

    shutil.copytree(examples_dir, tmp_path / "examples")
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        config_options.cwd = tmp_path
        yield pathlib.Path(old_cwd), tmp_path
    finally:
        os.chdir(old_cwd)


@pytest.fixture(name="runner_result")
def fixture_runner_result(
    config_options: Namespace,
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
            "examples/playbooks/nomatchestest.yml", 0, False, id="nomatchestest"
        ),
        pytest.param("examples/playbooks/unicode.yml", 1, False, id="unicode"),
        pytest.param(
            "examples/playbooks/lots_of_warnings.yml", 992, False, id="lots_of_warnings"
        ),
        pytest.param("examples/playbooks/become.yml", 0, False, id="become"),
        pytest.param(
            "examples/playbooks/contains_secrets.yml", 0, False, id="contains_secrets"
        ),
        pytest.param(
            "examples/playbooks/vars/empty_vars.yml", 0, False, id="empty_vars"
        ),
        pytest.param("examples/playbooks/vars/strings.yml", 0, True, id="strings"),
    ),
)
def test_transformer(  # pylint: disable=too-many-arguments, too-many-locals
    config_options: Namespace,
    copy_examples_dir: tuple[pathlib.Path, pathlib.Path],
    playbook: str,
    runner_result: LintResult,
    transformed: bool,
    matches_count: int,
) -> None:
    """
    Test that transformer can go through any corner cases.

    Based on TestRunner::test_runner
    """
    setattr(config_options, "write_list", ["all"])
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
