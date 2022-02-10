"""Tests for Transformer."""

from argparse import Namespace
from io import StringIO
from typing import Iterator, Optional, Tuple

import py
import pytest
from ruamel.yaml.emitter import Emitter
from ruamel.yaml.main import YAML

from ansiblelint.rules import RulesCollection

# noinspection PyProtectedMember
from ansiblelint.runner import LintResult, _get_matches
from ansiblelint.transformer import FormattedEmitter, Transformer


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
def runner_result(
    config_options: Namespace,
    default_rules_collection: RulesCollection,
    playbook: str,
) -> LintResult:
    """Fixture that runs the Runner to populate a LintResult for a given file."""
    config_options.lintables = [playbook]
    result = _get_matches(rules=default_rules_collection, options=config_options)
    return result


_input_playbook = [{"name": "playbook", "tasks": [{"name": "task"}]}]
_without_indents = """\
---
- name: playbook
  tasks:
  - name: task
"""
_with_indents = """\
---
  - name: playbook
    tasks:
      - name: task
"""
_with_indents_except_root_level = """\
---
- name: playbook
  tasks:
    - name: task
"""


@pytest.mark.parametrize(
    (
        "map_indent",
        "sequence_indent",
        "sequence_dash_offset",
        "alternate_emitter",
        "expected_output",
    ),
    (
        pytest.param(2, 2, 0, None, _without_indents, id="without_indents"),
        pytest.param(2, 4, 2, None, _with_indents, id="with_indents"),
        pytest.param(
            2,
            4,
            2,
            FormattedEmitter,
            _with_indents_except_root_level,
            id="with_indents_except_root_level",
        ),
    ),
)
def test_ruamel_yaml_sequence_formatting(
    map_indent: int,
    sequence_indent: int,
    sequence_dash_offset: int,
    alternate_emitter: Optional[Emitter],
    expected_output: str,
) -> None:
    """Test ``ruamel.yaml.YAML.dump()`` sequence formatting."""
    yaml = YAML(typ="rt")
    # NB: ruamel.yaml does not have typehints, so mypy complains about everything here.
    yaml.explicit_start = True  # type: ignore[assignment]
    yaml.map_indent = map_indent  # type: ignore[assignment]
    yaml.sequence_indent = sequence_indent  # type: ignore[assignment]
    yaml.sequence_dash_offset = sequence_dash_offset
    if alternate_emitter is not None:
        yaml.Emitter = alternate_emitter
    # ruamel.yaml only writes to a stream (there is no `dumps` function)
    with StringIO() as output:
        yaml.dump(_input_playbook, output)
        assert output.getvalue() == expected_output


@pytest.mark.parametrize(
    ("playbook", "matches_count", "transformed"),
    (
        # reuse TestRunner::test_runner test cases to ensure transformer does not mangle matches
        pytest.param(
            "examples/playbooks/nomatchestest.yml", 0, False, id="nomatchestest"
        ),
        pytest.param("examples/playbooks/unicode.yml", 1, False, id="unicode"),
        pytest.param(
            "examples/playbooks/lots_of_warnings.yml", 992, True, id="lots_of_warnings"
        ),
        pytest.param("examples/playbooks/become.yml", 0, True, id="become"),
        pytest.param(
            "examples/playbooks/contains_secrets.yml", 0, True, id="contains_secrets"
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
