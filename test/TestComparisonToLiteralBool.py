# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.ComparisonToLiteralBoolRule import ComparisonToLiteralBoolRule
from ansiblelint.testing import RunFromText

PASS_WHEN = '''
- name: example task
  debug:
    msg: test
  when: my_var

- name: another example task
  debug:
    msg: test
  when:
    - 1 + 1 == 2
    - true
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

- name: another example task
  debug:
    msg: test
  when:
    - my_var == false
'''


class TestComparisonToLiteralBoolRule(unittest.TestCase):
    collection = RulesCollection()
    collection.register(ComparisonToLiteralBoolRule())

    def setUp(self) -> None:
        self.runner = RunFromText(self.collection)

    def test_when(self) -> None:
        results = self.runner.run_role_tasks_main(PASS_WHEN)
        assert len(results) == 0

    def test_when_not_false(self) -> None:
        results = self.runner.run_role_tasks_main(PASS_WHEN_NOT_FALSE)
        assert len(results) == 0

    def test_when_not_null(self) -> None:
        results = self.runner.run_role_tasks_main(PASS_WHEN_NOT_NULL)
        assert len(results) == 0

    def test_literal_true(self) -> None:
        results = self.runner.run_role_tasks_main(FAIL_LITERAL_TRUE)
        assert len(results) == 1

    def test_literal_false(self) -> None:
        results = self.runner.run_role_tasks_main(FAIL_LITERAL_FALSE)
        assert len(results) == 2
