import unittest

from ansiblelint import RulesCollection
from ansiblelint.rules.LineTooLongRule import LineTooLongRule
from test import RunFromText

LONG_LINE = '''
- name: task example
  debug:
    msg: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua'
'''


class TestLineTooLongRule(unittest.TestCase):
    collection = RulesCollection()
    collection.register(LineTooLongRule())

    def setUp(self):
        self.runner = RunFromText(self.collection)

    def test_long_line(self):
        results = self.runner.run_role_tasks_main(LONG_LINE)
        self.assertEqual(1, len(results))
