# Copyright (c) 2016 Will Thames <will@thames.id.au>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""UseHandlerRatherThanWhenChangedRule used with ansible-lint."""
import sys
from typing import TYPE_CHECKING, Any, Dict, Union

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from typing import Optional

    from ansiblelint.file_utils import Lintable


def _changed_in_when(item: str) -> bool:
    item_list = item.split()

    if not isinstance(item, str) or 'and' in item_list:
        return False
    return any(
        changed in item
        for changed in [
            '.changed',
            '|changed',
            '["changed"]',
            "['changed']",
            "is changed",
        ]
    )


class UseHandlerRatherThanWhenChangedRule(AnsibleLintRule):
    id = 'no-handler'
    shortdesc = 'Tasks that run when changed should likely be handlers'
    description = (
        'If a task has a ``when: result.changed`` setting, it is effectively '
        'acting as a handler. You could use notify and move that task to '
        'handlers.'
    )
    link = "https://docs.ansible.com/ansible/latest/user_guide/playbooks_handlers.html"
    severity = 'MEDIUM'
    tags = ['idiom']
    version_added = 'historic'

    def matchtask(
        self, task: Dict[str, Any], file: 'Optional[Lintable]' = None
    ) -> Union[bool, str]:
        if task["__ansible_action_type__"] != 'task':
            return False

        when = task.get('when')

        if isinstance(when, list):
            for item in when:
                return _changed_in_when(item)
        if isinstance(when, str):
            return _changed_in_when(when)
        return False


if "pytest" in sys.modules:
    import pytest

    SUCCEED_CHANGED_WHEN = '''
- hosts: all
  tasks:
    - name: execute something
      command: echo 123
      register: result
      changed_when: true
'''

    SUCCEED_WHEN_AND = '''
- hosts: all
  tasks:
    - name: registering task 1
      command: echo Hello
      register: r1
      changed_when: true

    - name: registering task 2
      command: echo Hello
      register: r2
      changed_when: true

    - name: when task
      command: echo Hello
      when: r1.changed and r2.changed
'''

    FAIL_RESULT_IS_CHANGED = '''
- hosts: all
  tasks:
    - name: this should trigger no-handler rule
      command: echo could be done better
      when: result is changed
'''

    FAILED_SOMETHING_CHANGED = '''
- hosts: all
  tasks:
    - name: do anything
      command: echo 123
      when:
        - something.changed
'''

    @pytest.mark.parametrize(
        'rule_runner', (UseHandlerRatherThanWhenChangedRule,), indirect=['rule_runner']
    )
    def test_succeed_changed_when(rule_runner: Any) -> None:
        """Using changed_when is acceptable."""
        results = rule_runner.run_playbook(SUCCEED_CHANGED_WHEN)
        assert len(results) == 0

    @pytest.mark.parametrize(
        'rule_runner', (UseHandlerRatherThanWhenChangedRule,), indirect=['rule_runner']
    )
    def test_succeed_when_and(rule_runner: Any) -> None:
        """See https://github.com/ansible-community/ansible-lint/issues/1526."""
        results = rule_runner.run_playbook(SUCCEED_WHEN_AND)
        assert len(results) == 0

    @pytest.mark.parametrize(
        'rule_runner', (UseHandlerRatherThanWhenChangedRule,), indirect=['rule_runner']
    )
    def test_fail_result_is_changed(rule_runner: Any) -> None:
        """This task uses 'is changed'."""
        results = rule_runner.run_playbook(FAIL_RESULT_IS_CHANGED)
        assert len(results) == 1

    @pytest.mark.parametrize(
        'rule_runner', (UseHandlerRatherThanWhenChangedRule,), indirect=['rule_runner']
    )
    def test_failed_something_changed(rule_runner: Any) -> None:
        """This task uses '.changed'."""
        results = rule_runner.run_playbook(FAILED_SOMETHING_CHANGED)
        assert len(results) == 1
