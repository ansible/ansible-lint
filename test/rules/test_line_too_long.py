# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.YamllintRule import YamllintRule
from ansiblelint.testing import RunFromText

LONG_LINE = """\
---
- name: task example
  debug:
    msg: 'This is a very long text that is used in order to verify the rule that checks for very long lines. We do hope it was long enough to go over the line limit.'
"""  # noqa 501


class TestLineTooLongRule(unittest.TestCase):
    collection = RulesCollection()
    collection.register(YamllintRule())

    def setUp(self) -> None:
        self.runner = RunFromText(self.collection)

    def test_long_line(self) -> None:
        results = self.runner.run_role_tasks_main(LONG_LINE)
        assert len(results) == 1
