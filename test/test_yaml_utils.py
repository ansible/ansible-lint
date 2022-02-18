"""Tests for yaml-related utility functions."""
from io import StringIO
from typing import Any, Optional

import pytest
from ruamel.yaml.emitter import Emitter
from ruamel.yaml.main import YAML

import ansiblelint.yaml_utils
from ansiblelint.file_utils import Lintable


@pytest.fixture
def empty_lintable() -> Lintable:
    """Return a Lintable with no contents."""
    lintable = Lintable("__empty_file__")
    lintable._content = ""
    return lintable


def test_iter_tasks_in_file_with_empty_file(empty_lintable: Lintable) -> None:
    """Make sure that iter_tasks_in_file returns early when files are empty."""
    res = list(
        ansiblelint.yaml_utils.iter_tasks_in_file(empty_lintable, "some-rule-id")
    )
    assert res == []


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
_single_quote_without_indents = """\
---
- name: It's a playbook
  tasks:
  - name: '"fun" task'
    debug:
      msg: '{{ msg }}'
"""
_single_quote_with_indents = """\
---
  - name: It's a playbook
    tasks:
      - name: '"fun" task'
        debug:
          msg: '{{ msg }}'
"""
_double_quote_without_indents = """\
---
- name: It's a playbook
  tasks:
  - name: '"fun" task'
    debug:
      msg: "{{ msg }}"
"""
_double_quote_with_indents_except_root_level = """\
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
            _single_quote_without_indents,
            id="single_quote_without_indents",
        ),
        pytest.param(
            2,
            4,
            2,
            None,
            _single_quote_with_indents,
            id="single_quote_with_indents",
        ),
        pytest.param(
            2,
            2,
            0,
            ansiblelint.yaml_utils.FormattedEmitter,
            _double_quote_without_indents,
            id="double_quote_without_indents",
        ),
        pytest.param(
            2,
            4,
            2,
            ansiblelint.yaml_utils.FormattedEmitter,
            _double_quote_with_indents_except_root_level,
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
    # Ansible (via PyYAML) only supports YAML 1.1, so make sure to use that code path.
    yaml.version = (1, 1)  # type: ignore[assignment]
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
        # final_yaml_dump_transform strips the "%YAML 1.1" prefix
        output = ansiblelint.yaml_utils.final_yaml_dump_transform(
            output_stream.getvalue()
        )
        assert output == expected_output
