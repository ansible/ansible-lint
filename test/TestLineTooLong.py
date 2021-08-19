# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.YamllintRule import YamllintRule
from ansiblelint.testing import RunFromText

LONG_LINE = '''\
- name: task example
  debug:
    msg: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua tempor incididunt ut labore et dolore'
'''  # noqa 501


class TestLineTooLongRule(unittest.TestCase):
    collection = RulesCollection()
    collection.register(YamllintRule())

    def setUp(self) -> None:
        self.runner = RunFromText(self.collection)

    def test_long_line(self) -> None:
        results = self.runner.run_role_tasks_main(LONG_LINE)
        assert len(results) == 1
