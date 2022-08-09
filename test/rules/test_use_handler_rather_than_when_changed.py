"""Tests for no-handler rule."""
from ansiblelint.rules import RulesCollection
from ansiblelint.rules.no_handler import UseHandlerRatherThanWhenChangedRule
from ansiblelint.testing import RunFromText

SUCCESS_TASKS = """
- name: Print helpful error message
  debug:
    var: result
  when: result.failed

- name: Do something when hello is output
  debug:
    msg: why isn't this a handler
  when: result.stdout == "hello"

- name: Never actually debug
  debug:
    var: result
  when: False

- name: "Don't execute this step"
  debug:
    msg: "debug message"
  when:
    - false

- name: Check when with a list
  debug:
    var: result
  when:
  - conditionA
  - conditionB
"""


FAIL_TASKS = """
- name: Execute command
  command: echo hello
  register: result

- name: This should be a handler
  debug:
    msg: why isn't this a handler
  when: result.changed

- name: This should be a handler 2
  debug:
    msg: why isn't this a handler
  when: result|changed

- name: This should be a handler 3
  debug:
    msg: why isn't this a handler
  when: result.changed == true

- name: This should be a handler 4
  debug:
    msg: why isn't this a handler
  when: result['changed'] == true

- name: This should be a handler 5
  debug:
    msg: why isn't this a handler
  when:
  - result['changed'] == true
  - another_condition
"""


def test_no_handler_success() -> None:
    """Positive test for no-handler."""
    collection = RulesCollection()
    collection.register(UseHandlerRatherThanWhenChangedRule())
    runner = RunFromText(collection)
    results = runner.run_role_tasks_main(SUCCESS_TASKS)
    assert len(results) == 0


def test_no_handler_fail() -> None:
    """Negative test for no-handler."""
    collection = RulesCollection()
    collection.register(UseHandlerRatherThanWhenChangedRule())
    runner = RunFromText(collection)
    results = runner.run_role_tasks_main(FAIL_TASKS)
    assert len(results) == 5
