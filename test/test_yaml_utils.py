"""Tests for yaml-related utility functions."""
from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import Any

import pytest
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.emitter import Emitter
from ruamel.yaml.main import YAML
from yamllint.linter import run as run_yamllint

import ansiblelint.yaml_utils
from ansiblelint.file_utils import Lintable

fixtures_dir = Path(__file__).parent / "fixtures"
formatting_before_fixtures_dir = fixtures_dir / "formatting-before"
formatting_prettier_fixtures_dir = fixtures_dir / "formatting-prettier"
formatting_after_fixtures_dir = fixtures_dir / "formatting-after"


@pytest.fixture(name="empty_lintable")
def fixture_empty_lintable() -> Lintable:
    """Return a Lintable with no contents."""
    lintable = Lintable("__empty_file__.yaml")
    lintable._content = ""  # pylint: disable=protected-access
    return lintable


def test_iter_tasks_in_file_with_empty_file(empty_lintable: Lintable) -> None:
    """Make sure that iter_tasks_in_file returns early when files are empty."""
    res = list(ansiblelint.yaml_utils.iter_tasks_in_file(empty_lintable))
    assert not res


def test_nested_items_path() -> None:
    """Verify correct function of nested_items_path()."""
    data = {
        "foo": "text",
        "bar": {"some": "text2"},
        "fruits": ["apple", "orange"],
        "answer": [{"forty-two": ["life", "universe", "everything"]}],
    }

    items = [
        ("foo", "text", []),
        ("bar", {"some": "text2"}, []),
        ("some", "text2", ["bar"]),
        ("fruits", ["apple", "orange"], []),
        (0, "apple", ["fruits"]),
        (1, "orange", ["fruits"]),
        ("answer", [{"forty-two": ["life", "universe", "everything"]}], []),
        (0, {"forty-two": ["life", "universe", "everything"]}, ["answer"]),
        ("forty-two", ["life", "universe", "everything"], ["answer", 0]),
        (0, "life", ["answer", 0, "forty-two"]),
        (1, "universe", ["answer", 0, "forty-two"]),
        (2, "everything", ["answer", 0, "forty-two"]),
    ]
    assert list(ansiblelint.yaml_utils.nested_items_path(data)) == items


@pytest.mark.parametrize(
    "invalid_data_input",
    (
        "string",
        42,
        1.234,
        ("tuple",),
        {"set"},
        # NoneType is no longer include, as we assume we have to ignore it
    ),
)
def test_nested_items_path_raises_typeerror(invalid_data_input: Any) -> None:
    """Verify non-dict/non-list types make nested_items_path() raises TypeError."""
    with pytest.raises(TypeError, match=r"Expected a dict or a list.*"):
        list(ansiblelint.yaml_utils.nested_items_path(invalid_data_input))


_input_playbook = [
    {
        "name": "It's a playbook",  # unambiguous; no quotes needed
        "tasks": [
            {
                "name": '"fun" task',  # should be a single-quoted string
                "debug": {
                    # ruamel.yaml default to single-quotes
                    # our Emitter defaults to double-quotes
                    "msg": "{{ msg }}",
                },
            }
        ],
    }
]
_SINGLE_QUOTE_WITHOUT_INDENTS = """\
---
- name: It's a playbook
  tasks:
  - name: '"fun" task'
    debug:
      msg: '{{ msg }}'
"""
_SINGLE_QUOTE_WITH_INDENTS = """\
---
  - name: It's a playbook
    tasks:
      - name: '"fun" task'
        debug:
          msg: '{{ msg }}'
"""
_DOUBLE_QUOTE_WITHOUT_INDENTS = """\
---
- name: It's a playbook
  tasks:
  - name: '"fun" task'
    debug:
      msg: "{{ msg }}"
"""
_DOUBLE_QUOTE_WITH_INDENTS_EXCEPT_ROOT_LEVEL = """\
---
- name: It's a playbook
  tasks:
    - name: '"fun" task'
      debug:
        msg: "{{ msg }}"
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
        pytest.param(
            2,
            2,
            0,
            None,
            _SINGLE_QUOTE_WITHOUT_INDENTS,
            id="single_quote_without_indents",
        ),
        pytest.param(
            2,
            4,
            2,
            None,
            _SINGLE_QUOTE_WITH_INDENTS,
            id="single_quote_with_indents",
        ),
        pytest.param(
            2,
            2,
            0,
            ansiblelint.yaml_utils.FormattedEmitter,
            _DOUBLE_QUOTE_WITHOUT_INDENTS,
            id="double_quote_without_indents",
        ),
        pytest.param(
            2,
            4,
            2,
            ansiblelint.yaml_utils.FormattedEmitter,
            _DOUBLE_QUOTE_WITH_INDENTS_EXCEPT_ROOT_LEVEL,
            id="double_quote_with_indents_except_root_level",
        ),
    ),
)
def test_custom_ruamel_yaml_emitter(
    map_indent: int,
    sequence_indent: int,
    sequence_dash_offset: int,
    alternate_emitter: Emitter | None,
    expected_output: str,
) -> None:
    """Test ``ruamel.yaml.YAML.dump()`` sequence formatting and quotes."""
    yaml = YAML(typ="rt")
    # NB: ruamel.yaml does not have typehints, so mypy complains about everything here.
    yaml.explicit_start = True  # type: ignore[assignment]
    yaml.map_indent = map_indent  # type: ignore[assignment]
    yaml.sequence_indent = sequence_indent  # type: ignore[assignment]
    yaml.sequence_dash_offset = sequence_dash_offset
    if alternate_emitter is not None:
        yaml.Emitter = alternate_emitter
    # ruamel.yaml only writes to a stream (there is no `dumps` function)
    with StringIO() as output_stream:
        yaml.dump(_input_playbook, output_stream)
        output = output_stream.getvalue()
    assert output == expected_output


@pytest.fixture(name="yaml_formatting_fixtures")
def fixture_yaml_formatting_fixtures(fixture_filename: str) -> tuple[str, str, str]:
    """Get the contents for the formatting fixture files.

    To regenerate these fixtures, please run ``test/fixtures/test_regenerate_formatting_fixtures.py``.

    Ideally, prettier should not have to change any ``formatting-after`` fixtures.
    """
    before_path = formatting_before_fixtures_dir / fixture_filename
    prettier_path = formatting_prettier_fixtures_dir / fixture_filename
    after_path = formatting_after_fixtures_dir / fixture_filename
    before_content = before_path.read_text()
    prettier_content = prettier_path.read_text()
    formatted_content = after_path.read_text()
    return before_content, prettier_content, formatted_content


@pytest.mark.parametrize(
    "fixture_filename",
    (
        "fmt-1.yml",
        "fmt-2.yml",
        "fmt-3.yml",
    ),
)
def test_formatted_yaml_loader_dumper(
    yaml_formatting_fixtures: tuple[str, str, str],
    fixture_filename: str,
) -> None:
    """Ensure that FormattedYAML loads/dumps formatting fixtures consistently."""
    # pylint: disable=unused-argument
    before_content, prettier_content, after_content = yaml_formatting_fixtures
    assert before_content != prettier_content
    assert before_content != after_content

    yaml = ansiblelint.yaml_utils.FormattedYAML()

    data_before = yaml.loads(before_content)
    dump_from_before = yaml.dumps(data_before)
    data_prettier = yaml.loads(prettier_content)
    dump_from_prettier = yaml.dumps(data_prettier)
    data_after = yaml.loads(after_content)
    dump_from_after = yaml.dumps(data_after)

    # comparing data does not work because the Comment objects
    # have different IDs even if contents do not match.

    assert dump_from_before == after_content
    assert dump_from_prettier == after_content
    assert dump_from_after == after_content

    # We can't do this because FormattedYAML is stricter in some cases:
    # assert prettier_content == after_content
    #
    # Instead, `pytest --regenerate-formatting-fixtures` will fail if prettier would
    # change any files in test/fixtures/formatting-after

    # Running our files through yamllint, after we reformatted them,
    # should not yield any problems.
    config = ansiblelint.yaml_utils.load_yamllint_config()
    assert not list(run_yamllint(after_content, config))


@pytest.fixture(name="lintable")
def fixture_lintable(file_path: str) -> Lintable:
    """Return a playbook Lintable for use in ``get_path_to_*`` tests."""
    return Lintable(file_path)


@pytest.fixture(name="ruamel_data")
def fixture_ruamel_data(lintable: Lintable) -> CommentedMap | CommentedSeq:
    """Return the loaded YAML data for the Lintable."""
    yaml = ansiblelint.yaml_utils.FormattedYAML()
    data: CommentedMap | CommentedSeq = yaml.loads(lintable.content)
    return data


@pytest.mark.parametrize(
    ("file_path", "line_number", "expected_path"),
    (
        # ignored lintables
        pytest.param(
            "examples/playbooks/tasks/passing_task.yml", 2, [], id="ignore_tasks_file"
        ),
        pytest.param(
            "examples/roles/more_complex/handlers/main.yml",
            2,
            [],
            id="ignore_handlers_file",
        ),
        pytest.param("examples/playbooks/vars/other.yml", 2, [], id="ignore_vars_file"),
        pytest.param(
            "examples/host_vars/localhost.yml", 2, [], id="ignore_host_vars_file"
        ),
        pytest.param("examples/group_vars/all.yml", 2, [], id="ignore_group_vars_file"),
        pytest.param(
            "examples/inventory/inventory.yml", 2, [], id="ignore_inventory_file"
        ),
        pytest.param(
            "examples/roles/dependency_in_meta/meta/main.yml",
            2,
            [],
            id="ignore_meta_file",
        ),
        pytest.param(
            "examples/reqs_v1/requirements.yml", 2, [], id="ignore_requirements_v1_file"
        ),
        pytest.param(
            "examples/reqs_v2/requirements.yml", 2, [], id="ignore_requirements_v2_file"
        ),
        # we don't have any release notes examples. Oh well.
        # pytest.param("examples/", 2, [], id="ignore_release_notes_file"),
        pytest.param(
            ".pre-commit-config.yaml", 2, [], id="ignore_unrecognized_yaml_file"
        ),
        # playbook lintables
        pytest.param(
            "examples/playbooks/become.yml",
            1,
            [],
            id="1_play_playbook-line_before_play",
        ),
        pytest.param(
            "examples/playbooks/become.yml",
            2,
            [0],
            id="1_play_playbook-first_line_in_play",
        ),
        pytest.param(
            "examples/playbooks/become.yml",
            10,
            [0],
            id="1_play_playbook-middle_line_in_play",
        ),
        pytest.param(
            "examples/playbooks/become.yml",
            100,
            [0],
            id="1_play_playbook-line_after_eof",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            1,
            [],
            id="4_play_playbook-line_before_play_1",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            2,
            [0],
            id="4_play_playbook-first_line_in_play_1",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            5,
            [0],
            id="4_play_playbook-middle_line_in_play_1",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            9,
            [0],
            id="4_play_playbook-last_line_in_play_1",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            10,
            [1],
            id="4_play_playbook-first_line_in_play_2",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            14,
            [1],
            id="4_play_playbook-middle_line_in_play_2",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            18,
            [1],
            id="4_play_playbook-last_line_in_play_2",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            19,
            [2],
            id="4_play_playbook-first_line_in_play_3",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            23,
            [2],
            id="4_play_playbook-middle_line_in_play_3",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            27,
            [2],
            id="4_play_playbook-last_line_in_play_3",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            28,
            [3],
            id="4_play_playbook-first_line_in_play_4",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            31,
            [3],
            id="4_play_playbook-middle_line_in_play_4",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            35,
            [3],
            id="4_play_playbook-last_line_in_play_4",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            100,
            [3],
            id="4_play_playbook-line_after_eof",
        ),
        pytest.param(
            "examples/playbooks/playbook-parent.yml",
            1,
            [],
            id="import_playbook-line_before_play_1",
        ),
        pytest.param(
            "examples/playbooks/playbook-parent.yml",
            2,
            [0],
            id="import_playbook-first_line_in_play_1",
        ),
        pytest.param(
            "examples/playbooks/playbook-parent.yml",
            3,
            [0],
            id="import_playbook-middle_line_in_play_1",
        ),
        pytest.param(
            "examples/playbooks/playbook-parent.yml",
            4,
            [0],
            id="import_playbook-last_line_in_play_1",
        ),
        pytest.param(
            "examples/playbooks/playbook-parent.yml",
            5,
            [1],
            id="import_playbook-first_line_in_play_2",
        ),
        pytest.param(
            "examples/playbooks/playbook-parent.yml",
            6,
            [1],
            id="import_playbook-middle_line_in_play_2",
        ),
        pytest.param(
            "examples/playbooks/playbook-parent.yml",
            7,
            [1],
            id="import_playbook-last_line_in_play_2",
        ),
        pytest.param(
            "examples/playbooks/playbook-parent.yml",
            8,
            [2],
            id="import_playbook-first_line_in_play_3",
        ),
        pytest.param(
            "examples/playbooks/playbook-parent.yml",
            9,
            [2],
            id="import_playbook-last_line_in_play_3",
        ),
        pytest.param(
            "examples/playbooks/playbook-parent.yml",
            15,
            [2],
            id="import_playbook-line_after_eof",
        ),
    ),
)
def test_get_path_to_play(
    lintable: Lintable,
    line_number: int,
    ruamel_data: CommentedMap | CommentedSeq,
    expected_path: list[int | str],
) -> None:
    """Ensure ``get_path_to_play`` returns the expected path given a file + line."""
    path_to_play = ansiblelint.yaml_utils.get_path_to_play(
        lintable, line_number, ruamel_data
    )
    assert path_to_play == expected_path


@pytest.mark.parametrize(
    ("file_path", "line_number", "expected_path"),
    (
        # ignored lintables
        pytest.param("examples/playbooks/vars/other.yml", 2, [], id="ignore_vars_file"),
        pytest.param(
            "examples/host_vars/localhost.yml", 2, [], id="ignore_host_vars_file"
        ),
        pytest.param("examples/group_vars/all.yml", 2, [], id="ignore_group_vars_file"),
        pytest.param(
            "examples/inventory/inventory.yml", 2, [], id="ignore_inventory_file"
        ),
        pytest.param(
            "examples/roles/dependency_in_meta/meta/main.yml",
            2,
            [],
            id="ignore_meta_file",
        ),
        pytest.param(
            "examples/reqs_v1/requirements.yml", 2, [], id="ignore_requirements_v1_file"
        ),
        pytest.param(
            "examples/reqs_v2/requirements.yml", 2, [], id="ignore_requirements_v2_file"
        ),
        # we don't have any release notes examples. Oh well.
        # pytest.param("examples/", 2, [], id="ignore_release_notes_file"),
        pytest.param(
            ".pre-commit-config.yaml", 2, [], id="ignore_unrecognized_yaml_file"
        ),
        # tasks-containing lintables
        pytest.param(
            "examples/playbooks/become.yml",
            4,
            [],
            id="1_task_playbook-line_before_tasks",
        ),
        pytest.param(
            "examples/playbooks/become.yml",
            5,
            [0, "tasks", 0],
            id="1_task_playbook-first_line_in_task_1",
        ),
        pytest.param(
            "examples/playbooks/become.yml",
            10,
            [0, "tasks", 0],
            id="1_task_playbook-middle_line_in_task_1",
        ),
        pytest.param(
            "examples/playbooks/become.yml",
            15,
            [0, "tasks", 0],
            id="1_task_playbook-last_line_in_task_1",
        ),
        pytest.param(
            "examples/playbooks/become.yml",
            100,
            [0, "tasks", 0],
            id="1_task_playbook-line_after_eof_without_anything_after_task",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            1,
            [],
            id="4_play_playbook-play_1_line_before_tasks",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            7,
            [0, "tasks", 0],
            id="4_play_playbook-play_1_first_line_task_1",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            9,
            [0, "tasks", 0],
            id="4_play_playbook-play_1_last_line_task_1",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            10,
            [],
            id="4_play_playbook-play_2_line_before_tasks",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            12,
            [],
            id="4_play_playbook-play_2_line_before_tasks",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            13,
            [1, "tasks", 0],
            id="4_play_playbook-play_2_first_line_task_1",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            18,
            [1, "tasks", 0],
            id="4_play_playbook-play_2_middle_line_task_1",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            18,
            [1, "tasks", 0],
            id="4_play_playbook-play_2_last_line_task_1",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            19,
            [],
            id="4_play_playbook-play_3_line_before_tasks",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            22,
            [],
            id="4_play_playbook-play_3_line_before_tasks",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            23,
            [2, "tasks", 0],
            id="4_play_playbook-play_3_first_line_task_1",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            25,
            [2, "tasks", 0],
            id="4_play_playbook-play_3_middle_line_task_1",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            27,
            [2, "tasks", 0],
            id="4_play_playbook-play_3_last_line_task_1",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            28,
            [],
            id="4_play_playbook-play_4_line_before_tasks",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            31,
            [],
            id="4_play_playbook-play_4_line_before_tasks",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            32,
            [3, "tasks", 0],
            id="4_play_playbook-play_4_first_line_task_1",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            33,
            [3, "tasks", 0],
            id="4_play_playbook-play_4_middle_line_task_1",
        ),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            35,
            [3, "tasks", 0],
            id="4_play_playbook-play_4_last_line_task_1",
        ),
        # playbook with multiple tasks + tasks blocks in a play
        pytest.param(
            # must have at least one key after one of the tasks blocks
            "examples/playbooks/include.yml",
            6,
            [0, "pre_tasks", 0],
            id="playbook-multi_tasks_blocks-pre_tasks_last_task_before_roles",
        ),
        pytest.param(
            "examples/playbooks/include.yml",
            7,
            [],
            id="playbook-multi_tasks_blocks-roles_after_pre_tasks",
        ),
        pytest.param(
            "examples/playbooks/include.yml",
            10,
            [],
            id="playbook-multi_tasks_blocks-roles_before_tasks",
        ),
        pytest.param(
            "examples/playbooks/include.yml",
            12,
            [0, "tasks", 0],
            id="playbook-multi_tasks_blocks-tasks_first_task",
        ),
        pytest.param(
            "examples/playbooks/include.yml",
            14,
            [0, "tasks", 1],
            id="playbook-multi_tasks_blocks-tasks_last_task_before_handlers",
        ),
        pytest.param(
            "examples/playbooks/include.yml",
            16,
            [0, "handlers", 0],
            id="playbook-multi_tasks_blocks-handlers_task",
        ),
        # playbook with subtasks blocks
        pytest.param(
            "examples/playbooks/blockincludes.yml",
            14,
            [0, "tasks", 0, "block", 1, "block", 0],
            id="playbook-deeply_nested_task",
        ),
        pytest.param(
            "examples/playbooks/block.yml",
            12,
            [0, "tasks", 0, "block", 1],
            id="playbook-subtasks-block_task_2",
        ),
        pytest.param(
            "examples/playbooks/block.yml",
            22,
            [0, "tasks", 0, "rescue", 2],
            id="playbook-subtasks-rescue_task_3",
        ),
        pytest.param(
            "examples/playbooks/block.yml",
            25,
            [0, "tasks", 0, "always", 0],
            id="playbook-subtasks-always_task_3",
        ),
        # tasks files
        pytest.param("examples/playbooks/tasks/x.yml", 2, [0], id="tasks-null_task"),
        pytest.param(
            "examples/playbooks/tasks/x.yml", 6, [1], id="tasks-null_task_next"
        ),
        pytest.param(
            "examples/playbooks/tasks/empty_blocks.yml",
            7,
            [0],  # this IS part of the first task and "rescue" does not have subtasks.
            id="tasks-null_rescue",
        ),
        pytest.param(
            "examples/playbooks/tasks/empty_blocks.yml",
            8,
            [0],  # this IS part of the first task and "always" does not have subtasks.
            id="tasks-empty_always",
        ),
        pytest.param(
            "examples/playbooks/tasks/empty_blocks.yml",
            16,
            [1, "always", 0],
            id="tasks-task_beyond_empty_blocks",
        ),
        pytest.param(
            "examples/roles/more_complex/tasks/main.yml",
            1,
            [],
            id="tasks-line_before_tasks",
        ),
        pytest.param(
            "examples/roles/more_complex/tasks/main.yml",
            2,
            [0],
            id="tasks-first_line_in_task_1",
        ),
        pytest.param(
            "examples/roles/more_complex/tasks/main.yml",
            3,
            [0],
            id="tasks-middle_line_in_task_1",
        ),
        pytest.param(
            "examples/roles/more_complex/tasks/main.yml",
            4,
            [0],
            id="tasks-last_line_in_task_1",
        ),
        pytest.param(
            "examples/roles/more_complex/tasks/main.yml",
            5,
            [1],
            id="tasks-first_line_in_task_2",
        ),
        pytest.param(
            "examples/roles/more_complex/tasks/main.yml",
            6,
            [1],
            id="tasks-middle_line_in_task_2",
        ),
        pytest.param(
            "examples/roles/more_complex/tasks/main.yml",
            7,
            [1],
            id="tasks-last_line_in_task_2",
        ),
        pytest.param(
            "examples/roles/more_complex/tasks/main.yml",
            8,
            [2],
            id="tasks-first_line_in_task_3",
        ),
        pytest.param(
            "examples/roles/more_complex/tasks/main.yml",
            9,
            [2],
            id="tasks-last_line_in_task_3",
        ),
        pytest.param(
            "examples/roles/more_complex/tasks/main.yml",
            100,
            [2],
            id="tasks-line_after_eof",
        ),
        # handlers
        pytest.param(
            "examples/roles/more_complex/handlers/main.yml",
            1,
            [],
            id="handlers-line_before_tasks",
        ),
        pytest.param(
            "examples/roles/more_complex/handlers/main.yml",
            2,
            [0],
            id="handlers-first_line_in_task_1",
        ),
        pytest.param(
            "examples/roles/more_complex/handlers/main.yml",
            3,
            [0],
            id="handlers-last_line_in_task_1",
        ),
        pytest.param(
            "examples/roles/more_complex/handlers/main.yml",
            100,
            [0],
            id="handlers-line_after_eof",
        ),
    ),
)
def test_get_path_to_task(
    lintable: Lintable,
    line_number: int,
    ruamel_data: CommentedMap | CommentedSeq,
    expected_path: list[int | str],
) -> None:
    """Ensure ``get_task_to_play`` returns the expected path given a file + line."""
    path_to_task = ansiblelint.yaml_utils.get_path_to_task(
        lintable, line_number, ruamel_data
    )
    assert path_to_task == expected_path


@pytest.mark.parametrize(
    ("file_path", "line_number"),
    (
        pytest.param("examples/playbooks/become.yml", 0, id="1_play_playbook"),
        pytest.param(
            "examples/playbooks/rule-partial-become-without-become-pass.yml",
            0,
            id="4_play_playbook",
        ),
        pytest.param("examples/playbooks/playbook-parent.yml", 0, id="import_playbook"),
        pytest.param("examples/playbooks/become.yml", 0, id="1_task_playbook"),
    ),
)
def test_get_path_to_play_raises_value_error_for_bad_line_number(
    lintable: Lintable,
    line_number: int,
    ruamel_data: CommentedMap | CommentedSeq,
) -> None:
    """Ensure ``get_path_to_play`` raises ValueError for line_number < 1."""
    with pytest.raises(
        ValueError, match=f"expected line_number >= 1, got {line_number}"
    ):
        ansiblelint.yaml_utils.get_path_to_play(lintable, line_number, ruamel_data)


@pytest.mark.parametrize(
    ("file_path", "line_number"),
    (pytest.param("examples/roles/more_complex/tasks/main.yml", 0, id="tasks"),),
)
def test_get_path_to_task_raises_value_error_for_bad_line_number(
    lintable: Lintable,
    line_number: int,
    ruamel_data: CommentedMap | CommentedSeq,
) -> None:
    """Ensure ``get_task_to_play`` raises ValueError for line_number < 1."""
    with pytest.raises(
        ValueError, match=f"expected line_number >= 1, got {line_number}"
    ):
        ansiblelint.yaml_utils.get_path_to_task(lintable, line_number, ruamel_data)


@pytest.mark.parametrize(
    ("before", "after"),
    (
        pytest.param(None, None, id="1"),
        pytest.param(1, 1, id="2"),
        pytest.param({}, {}, id="3"),
        pytest.param({"__file__": 1}, {}, id="simple"),
        pytest.param({"foo": {"__file__": 1}}, {"foo": {}}, id="nested"),
        pytest.param([{"foo": {"__file__": 1}}], [{"foo": {}}], id="nested-in-lint"),
        pytest.param({"foo": [{"__file__": 1}]}, {"foo": [{}]}, id="nested-in-lint"),
    ),
)
def test_deannotate(
    before: Any,
    after: Any,
) -> None:
    """Ensure deannotate works as intended."""
    assert ansiblelint.yaml_utils.deannotate(before) == after
