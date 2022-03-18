"""Validate ansiblelint.skip_utils."""
import pytest

from ansiblelint.skip_utils import get_rule_skips_from_line
from ansiblelint.testing import RunFromText

PLAYBOOK_WITH_NOQA = """\
---
- hosts: all
  vars:
    SOME_VAR_NOQA: "Foo"  # noqa var-naming
    SOME_VAR: "Bar"
  tasks:
    - name: "Set the SOME_OTHER_VAR"
      ansible.builtin.set_fact:
        SOME_OTHER_VAR_NOQA: "Baz"  # noqa var-naming
        SOME_OTHER_VAR: "Bat"
"""


@pytest.mark.parametrize(
    ("line", "expected"),
    (
        ("foo # noqa: bar", "bar"),
        ("foo # noqa bar", "bar"),
    ),
)
def test_get_rule_skips_from_line(line: str, expected: str) -> None:
    """Validate get_rule_skips_from_line."""
    v = get_rule_skips_from_line(line)
    assert v == [expected]


def test_playbook_noqa(default_text_runner: RunFromText) -> None:
    """Check that noqa is properly taken into account on vars and tasks."""
    results = default_text_runner.run_playbook(PLAYBOOK_WITH_NOQA)
    assert len(results) == 2
