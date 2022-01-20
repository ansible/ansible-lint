"""Tests for Transformer."""

import os
from argparse import Namespace
from typing import Any, Dict, Iterator, List, Tuple

import py
import pytest

from ansiblelint.constants import DEFAULT_RULESDIR
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
    oldcwd = tmpdir.chdir()
    config_options.cwd = tmpdir
    yield oldcwd, tmpdir
    oldcwd.chdir()


@pytest.fixture
def config_options(config_options: Namespace, opts: Dict[str, Any]) -> Namespace:
    # mirror default_rules_collection fixture setting
    config_options.enable_list = ['no-same-owner', 'facts-namespacing']

    # our defaults
    config_options.fmt_all_files = True

    # per-test option overrides
    # opt is an option name in ansiblelint.config.options
    for opt, value in opts.items():
        if isinstance(value, list):
            getattr(config_options, opt).extend(value)
        else:
            setattr(config_options, opt, value)
    yield config_options


@pytest.fixture
def rules_collection(config_options: Namespace) -> RulesCollection:
    """Return default rule collection."""
    assert os.path.isdir(DEFAULT_RULESDIR)
    return RulesCollection(rulesdirs=[DEFAULT_RULESDIR], options=config_options)


@pytest.fixture
def runner_result(
    config_options: Namespace,
    rules_collection: RulesCollection,
    playbook: str,
    exclude: List[str],
) -> LintResult:
    """Fixture that runs the Runner to populate a LintResult for a given file."""
    config_options.lintables = [playbook]
    config_options.exclude_paths = exclude
    result = _get_matches(rules=rules_collection, options=config_options)
    return result


# pylint: disable=too-many-arguments,too-many-locals
@pytest.mark.parametrize(
    ('playbook', 'exclude', 'matches_count', 'fixed_count', 'transformed', 'opts'),
    (
        # reuse TestRunner::test_runner test cases to ensure transformer does not mangle matches
        pytest.param(
            'examples/playbooks/nomatchestest.yml',
            [],
            0,
            0,
            False,
            {},
            id="nomatchestest",
        ),
        pytest.param(
            'examples/playbooks/unicode.yml', [], 1, 0, False, {}, id="unicode"
        ),
        pytest.param(
            'examples/playbooks/lots_of_warnings.yml',
            ['examples/playbooks/lots_of_warnings.yml'],
            0,
            0,
            False,
            {},
            id="lots_of_warnings",
        ),
        pytest.param('examples/playbooks/become.yml', [], 0, 0, True, {}, id="become"),
        pytest.param(
            'examples/playbooks/contains_secrets.yml',
            [],
            0,
            0,
            True,
            {},
            id="contains_secrets",
        ),
        # Transformer specific test cases
        pytest.param(
            'examples/playbooks/using-bare-variables-failure.yml',
            [],
            11,
            11,
            True,
            {},
            id="bare_vars_failure",
        ),
        pytest.param(
            'examples/playbooks/tasks/literal-bool-comparison.yml',
            [],
            6,
            6,
            True,
            {},
            id="literal_bool_comparison",
        ),
        pytest.param(
            'examples/playbooks/tasks/local_action.yml',
            [],
            2,
            2,
            True,
            {},
            id="local_action_replacement",
        ),
        pytest.param(
            'examples/playbooks/jinja2-when-failure.yml',
            ["examples/playbooks/roles/"],
            2,
            2,
            True,
            {},
            id="unwrap_jinja_when",
        ),
        pytest.param(
            'examples/playbooks/tasks/role-relative-paths.yml',
            [],
            4,
            4,
            True,
            {},
            id="fix_relative_role_paths",
        ),
        pytest.param(
            'examples/playbooks/task-has-name-failure.yml',
            [],
            4 + 2,  # 4 unnamed-task, 2 no-changed-when
            0,  # should not fix any unnamed-task
            True,
            {},
            id="stub_task_names",
        ),
        pytest.param(
            'examples/playbooks/var-spacing.yml',
            [],
            5,
            5,
            True,
            {},
            id="jinja_var_spacing",
        ),
        pytest.param(
            'examples/roles/role_for_no_action_shorthand/tasks/fail.yml',
            [],
            3,
            3,
            True,
            {},
            id="no_action_shorthand",
        ),
        pytest.param(
            'examples/roles/role_for_jinja_tests_as_filters/tasks/fail.yml',
            [],
            19,
            19,
            True,
            {},
            id="jinja_tests_are_not_filters_in_tasks",
        ),
        pytest.param(
            'examples/roles/role_for_jinja_tests_as_filters/templates/sample.ini.j2',
            [],
            2,
            2,
            True,
            {},
            id="jinja_tests_are_not_filters_in_template",
        ),
        pytest.param(
            'examples/roles/role_for_facts_namespacing/tasks/fail.yml',
            [],
            7,
            7,
            True,
            {},
            id="facts_namespacing_tasks",
        ),
        pytest.param(
            'examples/roles/role_for_facts_namespacing/templates/sample.ini.j2',
            [],
            6,
            6,
            True,
            {},
            id="facts_namespacing_template",
        ),
        pytest.param(
            'examples/playbooks/with-loops.yml',
            [],
            10,
            10,
            True,
            {"enable_list": ["no-with-loops"]},
            id="no_with_loops",
        ),
    ),
)
def test_transformer(
    copy_examples_dir: Tuple[py.path.local, py.path.local],
    playbook: str,
    config_options: Namespace,
    runner_result: LintResult,
    transformed: bool,
    matches_count: int,
    fixed_count: int,
) -> None:
    """
    Test that transformer can go through any corner cases.

    Based on TestRunner::test_runner
    """
    transformer = Transformer(result=runner_result)
    transformer.run(fmt_all_files=config_options.fmt_all_files)

    matches = runner_result.matches
    assert len(matches) == matches_count

    fixed = [match for match in matches if match.fixed]
    assert len(fixed) == fixed_count

    orig_dir, tmp_dir = copy_examples_dir
    orig_playbook = orig_dir / playbook
    expected_playbook = orig_dir / playbook.replace(
        orig_playbook.ext, f".transformed{orig_playbook.ext}"
    )
    transformed_playbook = tmp_dir / playbook

    orig_playbook_content = orig_playbook.read()
    expected_playbook_content = expected_playbook.read()
    transformed_playbook_content = transformed_playbook.read()

    if transformed:
        assert orig_playbook_content != transformed_playbook_content
    else:
        assert orig_playbook_content == transformed_playbook_content

    assert transformed_playbook_content == expected_playbook_content
