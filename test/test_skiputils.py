"""Validate ansiblelint.skip_utils."""
import pytest

from ansiblelint.skip_utils import get_rule_skips_from_line
from ansiblelint.testing import RunFromText

PLAYBOOK_WITH_NOQA = """\
- hosts: all
  vars:
    SOMEVARNOQA: "Foo"  # noqa var-naming
    SOMEVAR: "Bar"
  tasks:
    - name: "Set the SOMEOTHERVAR"
      set_fact:
        SOMEOTHERVARNOQA: "Baz"  # noqa var-naming
        SOMEOTHERVAR: "Bat"
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
    x = get_rule_skips_from_line(line)
    assert x == [expected]


def test_playbook_noqa(default_text_runner: RunFromText) -> None:
    """Check that noqa is properly taken into account on vars and tasks."""
    results = default_text_runner.run_playbook(PLAYBOOK_WITH_NOQA)
    assert len(results) == 2
