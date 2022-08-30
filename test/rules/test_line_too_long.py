"""Tests for line-too-long rule."""
from ansiblelint.rules import RulesCollection
from ansiblelint.rules.yaml_rule import YamllintRule
from ansiblelint.testing import RunFromText

LONG_LINE = """\
---
- name: Task example
  debug:
    msg: 'This is a very long text that is used in order to verify the rule that checks for very long lines. We do hope it was long enough to go over the line limit.'
"""  # noqa 501


def test_long_line() -> None:
    """Negative test for long-line."""
    collection = RulesCollection()
    collection.register(YamllintRule())
    runner = RunFromText(collection)
    results = runner.run_role_tasks_main(LONG_LINE)
    assert len(results) == 1
