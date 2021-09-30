# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.UseHandlerRatherThanWhenChangedRule import (
    UseHandlerRatherThanWhenChangedRule,
)
from ansiblelint.testing import RunFromText

SUCCESS_TASKS = '''
- name: print helpful error message
  debug:
    var: result
  when: result.failed

- name: do something when hello is output
  debug:
    msg: why isn't this a handler
  when: result.stdout == "hello"

- name: never actually debug
  debug:
    var: result
  when: False

- name: Dont execute this step
  debug:
    msg: "debug message"
  when:
    - false

- name: check when with a list
  debug:
    var: result
  when:
  - conditionA
  - conditionB
'''


FAIL_TASKS = '''
- name: execute command
  command: echo hello
  register: result

- name: this should be a handler
  debug:
    msg: why isn't this a handler
  when: result.changed

- name: this should be a handler 2
  debug:
    msg: why isn't this a handler
  when: result|changed

- name: this should be a handler 3
  debug:
    msg: why isn't this a handler
  when: result.changed == true

- name: this should be a handler 4
  debug:
    msg: why isn't this a handler
  when: result['changed'] == true

- name: this should be a handler 5
  debug:
    msg: why isn't this a handler
  when:
  - result['changed'] == true
  - another_condition
'''


class TestUseHandlerRatherThanWhenChanged(unittest.TestCase):
    collection = RulesCollection()
    collection.register(UseHandlerRatherThanWhenChangedRule())

    def setUp(self) -> None:
        self.runner = RunFromText(self.collection)

    def test_success(self) -> None:
        results = self.runner.run_role_tasks_main(SUCCESS_TASKS)
        assert len(results) == 0

    def test_fail(self) -> None:
        results = self.runner.run_role_tasks_main(FAIL_TASKS)
        assert len(results) == 5
