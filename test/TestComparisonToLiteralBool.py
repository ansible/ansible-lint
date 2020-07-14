import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.ComparisonToLiteralBoolRule import ComparisonToLiteralBoolRule

from . import RunFromText

PASS_WHEN = '''
- name: example task
  debug:
    msg: test
  when: my_var
'''

PASS_WHEN_NOT_FALSE = '''
- name: example task
  debug:
    msg: test
  when: not my_var
'''

PASS_WHEN_NOT_NULL = '''
- name: example task
  debug:
    msg: test
  when: my_var not None
'''

FAIL_LITERAL_TRUE = '''
- name: example task
  debug:
    msg: test
  when: my_var == True
'''

FAIL_LITERAL_FALSE = '''
- name: example task
  debug:
    msg: test
  when: my_var == false
'''


class TestComparisonToLiteralBoolRule(unittest.TestCase):
    collection = RulesCollection()
    collection.register(ComparisonToLiteralBoolRule())

    def setUp(self):
        self.runner = RunFromText(self.collection)

    def test_when(self):
        results = self.runner.run_role_tasks_main(PASS_WHEN)
        self.assertEqual(0, len(results))

    def test_when_not_false(self):
        results = self.runner.run_role_tasks_main(PASS_WHEN_NOT_FALSE)
        self.assertEqual(0, len(results))

    def test_when_not_null(self):
        results = self.runner.run_role_tasks_main(PASS_WHEN_NOT_NULL)
        self.assertEqual(0, len(results))

    def test_literal_true(self):
        results = self.runner.run_role_tasks_main(FAIL_LITERAL_TRUE)
        self.assertEqual(1, len(results))

    def test_literal_false(self):
        results = self.runner.run_role_tasks_main(FAIL_LITERAL_FALSE)
        self.assertEqual(1, len(results))
