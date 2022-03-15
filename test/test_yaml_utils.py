"""Tests for yaml-related utility functions."""
from io import StringIO
from pathlib import Path
from typing import Any, Optional, Tuple

import pytest
from ruamel.yaml.emitter import Emitter
from ruamel.yaml.main import YAML

import ansiblelint.yaml_utils
from ansiblelint.file_utils import Lintable

fixtures_dir = Path(__file__).parent / "fixtures"
formatting_before_fixtures_dir = fixtures_dir / "formatting-before"
formatting_prettier_fixtures_dir = fixtures_dir / "formatting-prettier"
formatting_after_fixtures_dir = fixtures_dir / "formatting-after"


@pytest.fixture(name="empty_lintable")
def fixture_empty_lintable() -> Lintable:
    """Return a Lintable with no contents."""
    lintable = Lintable("__empty_file__")
    lintable._content = ""  # pylint: disable=protected-access
    return lintable


def test_iter_tasks_in_file_with_empty_file(empty_lintable: Lintable) -> None:
    """Make sure that iter_tasks_in_file returns early when files are empty."""
    res = list(
        ansiblelint.yaml_utils.iter_tasks_in_file(empty_lintable, "some-rule-id")
    )
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
        None,
        ("tuple",),
        {"set"},
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
    alternate_emitter: Optional[Emitter],
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
def fixture_yaml_formatting_fixtures(fixture_filename: str) -> Tuple[str, str, str]:
    """Get the contents for the formatting fixture files.

    To regenerate these fixtures, please run ``tools/generate-formatting-fixtures.py``.

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
    ),
)
def test_formatted_yaml_loader_dumper(
    yaml_formatting_fixtures: Tuple[str, str, str],
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
