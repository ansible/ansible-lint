import unittest

from ansiblelint import RulesCollection
from ansiblelint.rules.VariableHasSpacesRule import VariableHasSpacesRule
from test import RunFromText

TASK_VARIABLES = '''
- name: variable example
  debug:
    msg: "{{ good_format }}"
- name: variable example
  debug:
    msg: "{{bad_format}}"
- name: variable example
  debug:
    msg: "{{ bad_format}}"
- name: variable example
  debug:
    msg: "{{bad_format }}"
'''


class TestVariableHasSpaces(unittest.TestCase):
    collection = RulesCollection()
    collection.register(VariableHasSpacesRule())

    def setUp(self):
        self.runner = RunFromText(self.collection)

    def test_variable_has_spaces(self):
        results = self.runner.run_role_tasks_main(TASK_VARIABLES)
        self.assertEqual(3, len(results))
