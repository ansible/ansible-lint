"""Tests for Transformer."""

from argparse import Namespace
from typing import Iterator, Tuple

import py
import pytest

from ansiblelint.rules import RulesCollection

# noinspection PyProtectedMember
from ansiblelint.runner import LintResult, _get_matches
from ansiblelint.transformer import Transformer


@pytest.fixture
def copy_examples_dir(
    tmpdir: py.path.local, config_options: Namespace
) -> Iterator[Tuple[py.path.local, py.path.local]]:
    """Fixture that copies the examples/ dir into a tmpdir."""
    examples_dir = py.path.local("examples")
    examples_dir.copy(tmpdir / "examples")
    old_cwd = tmpdir.chdir()
    config_options.cwd = tmpdir
    yield old_cwd, tmpdir
    old_cwd.chdir()


@pytest.fixture
def runner_result(
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
    ),
)
def test_transformer(
    copy_examples_dir: Tuple[py.path.local, py.path.local],
    playbook: str,
    runner_result: LintResult,
    transformed: bool,
    matches_count: int,
) -> None:
    """
    Test that transformer can go through any corner cases.

    Based on TestRunner::test_runner
    """
    transformer = Transformer(result=runner_result)
    transformer.run()

    matches = runner_result.matches
    assert len(matches) == matches_count

    orig_dir, tmp_dir = copy_examples_dir
    orig_playbook = orig_dir / playbook
    expected_playbook = orig_dir / playbook.replace(".yml", ".transformed.yml")
    transformed_playbook = tmp_dir / playbook

    orig_playbook_content = orig_playbook.read()
    expected_playbook_content = expected_playbook.read()
    transformed_playbook_content = transformed_playbook.read()

    if transformed:
        assert orig_playbook_content != transformed_playbook_content
    else:
        assert orig_playbook_content == transformed_playbook_content

    assert transformed_playbook_content == expected_playbook_content
