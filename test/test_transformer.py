import os
from argparse import Namespace
from typing import List, Tuple

import py
import pytest

from ansiblelint.cli import abspath
from ansiblelint.rules import RulesCollection

# noinspection PyProtectedMember
from ansiblelint.runner import _get_matches, LintResult
from ansiblelint.transformer import Transformer
from ansiblelint.transforms import TransformsCollection


@pytest.fixture
def copy_examples_dir(
    tmpdir: py.path.local, config_options: Namespace
) -> Tuple[py.path.local, py.path.local]:
    examples_dir = py.path.local("examples")
    examples_dir.copy(tmpdir / "examples")
    oldcwd = tmpdir.chdir()
    config_options.cwd = tmpdir
    yield oldcwd, tmpdir
    oldcwd.chdir()


@pytest.fixture
def runner_result(
    config_options: Namespace,
    default_rules_collection: RulesCollection,
    playbook: str,
    exclude: List[str],
) -> LintResult:
    config_options.lintables = [playbook]
    config_options.exclude_paths = exclude
    result = _get_matches(rules=default_rules_collection, options=config_options)
    return result


@pytest.mark.parametrize(
    ('playbook', 'exclude', 'matches_count', 'fixed_count', 'transformed'),
    (
        # reuse TestRunner::test_runner test cases to ensure transformer does not mangle matches
        pytest.param(
            'examples/playbooks/nomatchestest.yml', [], 0, 0, False, id="nomatchestest"
        ),
        pytest.param('examples/playbooks/unicode.yml', [], 1, 0, False, id="unicode"),
        pytest.param(
            'examples/playbooks/lots_of_warnings.yml',
            ['examples/playbooks/lots_of_warnings.yml'],
            0,
            0,
            False,
            id="lots_of_warnings",
        ),
        pytest.param('examples/playbooks/become.yml', [], 0, 0, True, id="become"),
        pytest.param(
            'examples/playbooks/contains_secrets.yml',
            [],
            0,
            0,
            True,
            id="contains_secrets",
        ),
        # Transformer specific test cases
        pytest.param(
            'examples/playbooks/using-bare-variables-failure.yml',
            [],
            11,
            11,
            True,
            id="bare_vars_failure",
        ),
    ),
)
def test_transformer(
    copy_examples_dir: Tuple[py.path.local, py.path.local],
    playbook: str,
    config_options: Namespace,
    default_transforms_collection: TransformsCollection,
    runner_result: LintResult,
    transformed: bool,
    matches_count: int,
    fixed_count: int,
) -> None:
    """
    Test that transformer can go through any corner cases.

    Based on TestRunner::test_runner
    """
    config_options.fmt_all_files = True  # TODO: make configurable

    transformer = Transformer(
        result=runner_result, transforms=default_transforms_collection
    )
    transformer.run(fmt_all_files=config_options.fmt_all_files)

    matches = runner_result.matches
    assert len(matches) == matches_count

    fixed = [match for match in matches if match.fixed]
    assert len(fixed) == fixed_count

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
