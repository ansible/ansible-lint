import unittest

from ansiblelint import RulesCollection
from ansiblelint.rules.VariableHasSpacesRule import VariableHasSpacesRule
from test import RunFromText

TASK_VARIABLES = '''
- name: good variable format
  debug:
    msg: "{{ good_format }}"
- name: good variable format
  debug:
    msg: "Value: {{ good_format }}"
- name: jinja escaping allowed
  debug:
    msg: "{{ '{{' }}"
- name: jinja escaping allowed
  shell: docker info --format '{{ '{{' }}json .Swarm.LocalNodeState{{ '}}' }}' | tr -d '"'
- name: jinja whitespace control allowed
  debug:
    msg: |
      {{ good_format }}/
      {{- good_format }}
      {{- good_format -}}
- name: bad variable format
  debug:
    msg: "{{bad_format}}"
- name: bad variable format
  debug:
    msg: "Value: {{ bad_format}}"
- name: bad variable format
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
