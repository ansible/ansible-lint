"""Tests for Transformer."""

from io import StringIO
from typing import Optional

import pytest
from ruamel.yaml.emitter import Emitter
from ruamel.yaml.main import YAML

# noinspection PyProtectedMember
from ansiblelint.transformer import FormattedEmitter, _final_yaml_transform

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
            FormattedEmitter,
            _double_quote_without_indents,
            id="double_quote_without_indents",
        ),
        pytest.param(
            2,
            4,
            2,
            FormattedEmitter,
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
        # _final_yaml_transform strips the "%YAML 1.1" prefix
        output = _final_yaml_transform(output_stream.getvalue())
        assert output == expected_output
