# Copyright 2018, Rackspace US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""NoLogPasswordsRule used with ansible-lint."""
import sys
from typing import TYPE_CHECKING, Any, Dict, Union

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.testing import RunFromText
from ansiblelint.utils import convert_to_boolean

if TYPE_CHECKING:
    from typing import Optional

    from ansiblelint.file_utils import Lintable


class NoLogPasswordsRule(AnsibleLintRule):
    """Describe and test the NoLogPasswordsRule."""

    id = "no-log-password"
    shortdesc = "password should not be logged."
    description = (
        "When passing password argument you should have no_log configured "
        "to a non False value to avoid accidental leaking of secrets."
    )
    severity = 'LOW'
    tags = ["opt-in", "security", "experimental"]
    version_added = "v5.0.9"

    def matchtask(
        self, task: Dict[str, Any], file: 'Optional[Lintable]' = None
    ) -> Union[bool, str]:

        if task["action"]["__ansible_module__"] == 'user' and (
            (
                task['action'].get('password_lock')
                or task['action'].get('password_lock') is False
            )
            and not task['action'].get('password')
        ):
            has_password = False
        else:
            for param in task["action"].keys():
                if 'password' in param:
                    has_password = True
                    break
            else:
                has_password = False

        has_loop = [key for key in task if key.startswith("with_") or key == 'loop']
        # No no_log and no_log: False behave the same way
        # and should return a failure (return True), so we
        # need to invert the boolean
        return bool(
            has_password
            and not convert_to_boolean(task.get('no_log', False))
            and len(has_loop) > 0
        )


if "pytest" in sys.modules:
    import pytest

    NO_LOG_UNUSED = '''
- hosts: all
  tasks:
    - name: Succeed when no_log is not used but no loop present
      user:
        name: bidule
        password: "wow"
        state: absent
'''

    NO_LOG_FALSE = '''
- hosts: all
  tasks:
    - name: Fail when no_log is set to False
      user:
        name: bidule
        user_password: "{{ item }}"
        state: absent
      with_items:
        - wow
        - now
      no_log: False
'''

    NO_LOG_NO = '''
- hosts: all
  tasks:
    - name: Fail when no_log is set to no
      user:
        name: bidule
        password: "{{ item }}"
        state: absent
      no_log: no
      loop:
        - wow
        - now
'''

    PASSWORD_WITH_LOCK = '''
- hosts: all
  tasks:
    - name: Fail when password is set and password_lock is true
      user:
        name: "{{ item }}"
        password: "wow"
        password_lock: true
      with_random_choice:
        - ansible
        - lint
'''

    NO_LOG_YES = '''
- hosts: all
  tasks:
    - name: Succeed when no_log is set to yes
      with_list:
        - name: user
          password: wow
        - password: now
          name: ansible
      user:
        name: "{{ item.name }}"
        password: "{{ item.password }}"
        state: absent
      no_log: yes
'''

    NO_LOG_TRUE = '''
- hosts: all
  tasks:
    - name: Succeed when no_log is set to True
      user:
        name: bidule
        user_password: "{{ item }}"
        state: absent
      no_log: True
      loop:
        - wow
        - now
'''

    PASSWORD_LOCK_YES = '''
- hosts: all
  tasks:
    - name: Succeed when only password locking account
      user:
        name: "{{ item }}"
        password_lock: yes
        # user_password: "this is a comment, not a password"
        with_list:
          - ansible
          - lint
'''

    PASSWORD_LOCK_FALSE = '''
- hosts: all
  tasks:
    - name: Succeed when password_lock is false and password is not used
      user:
        name: lint
        password_lock: False
'''

    @pytest.mark.parametrize(
        'rule_runner', (NoLogPasswordsRule,), indirect=['rule_runner']
    )
    def test_no_log_unused(rule_runner: RunFromText) -> None:
        """The task does not use no_log but also no loop."""
        results = rule_runner.run_playbook(NO_LOG_UNUSED)
        assert len(results) == 0

    @pytest.mark.parametrize(
        'rule_runner', (NoLogPasswordsRule,), indirect=['rule_runner']
    )
    def test_no_log_false(rule_runner: RunFromText) -> None:
        """The task sets no_log to false."""
        results = rule_runner.run_playbook(NO_LOG_FALSE)
        assert len(results) == 1

    @pytest.mark.parametrize(
        'rule_runner', (NoLogPasswordsRule,), indirect=['rule_runner']
    )
    def test_no_log_no(rule_runner: RunFromText) -> None:
        """The task sets no_log to no."""
        results = rule_runner.run_playbook(NO_LOG_NO)
        assert len(results) == 1

    @pytest.mark.parametrize(
        'rule_runner', (NoLogPasswordsRule,), indirect=['rule_runner']
    )
    def test_password_with_lock(rule_runner: RunFromText) -> None:
        """The task sets a password but also lock the user."""
        results = rule_runner.run_playbook(PASSWORD_WITH_LOCK)
        assert len(results) == 1

    @pytest.mark.parametrize(
        'rule_runner', (NoLogPasswordsRule,), indirect=['rule_runner']
    )
    def test_no_log_yes(rule_runner: RunFromText) -> None:
        """The task sets no_log to yes."""
        results = rule_runner.run_playbook(NO_LOG_YES)
        assert len(results) == 0

    @pytest.mark.parametrize(
        'rule_runner', (NoLogPasswordsRule,), indirect=['rule_runner']
    )
    def test_no_log_true(rule_runner: RunFromText) -> None:
        """The task sets no_log to true."""
        results = rule_runner.run_playbook(NO_LOG_TRUE)
        assert len(results) == 0

    @pytest.mark.parametrize(
        'rule_runner', (NoLogPasswordsRule,), indirect=['rule_runner']
    )
    def test_password_lock_yes(rule_runner: RunFromText) -> None:
        """The task only locks the user."""
        results = rule_runner.run_playbook(PASSWORD_LOCK_YES)
        assert len(results) == 0

    @pytest.mark.parametrize(
        'rule_runner', (NoLogPasswordsRule,), indirect=['rule_runner']
    )
    def test_password_lock_false(rule_runner: RunFromText) -> None:
        """The task does not actually lock the user."""
        results = rule_runner.run_playbook(PASSWORD_LOCK_FALSE)
        assert len(results) == 0
