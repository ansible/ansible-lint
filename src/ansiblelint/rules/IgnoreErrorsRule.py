"""IgnoreErrorsRule used with ansible-lint."""
import sys
from typing import TYPE_CHECKING, Any, Dict, Union

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.testing import RunFromText

if TYPE_CHECKING:
    from typing import Optional

    from ansiblelint.file_utils import Lintable


class IgnoreErrorsRule(AnsibleLintRule):
    """Describe and test the IgnoreErrorsRule."""

    id = "ignore-errors"
    shortdesc = (
        'Use failed_when and specify error conditions instead of using ignore_errors'
    )
    description = (
        'Instead of ignoring all errors, ignore the errors only when using ``{{ ansible_check_mode }}``, '
        'register the errors using ``register``, '
        'or use ``failed_when:`` and specify acceptable error conditions '
        'to reduce the risk of ignoring important failures.'
    )
    severity = 'LOW'
    tags = ['unpredictability', 'experimental']
    version_added = 'v5.0.7'

    def matchtask(
        self, task: Dict[str, Any], file: 'Optional[Lintable]' = None
    ) -> Union[bool, str]:
        if (
            task.get("ignore_errors")
            and task.get("ignore_errors") != "{{ ansible_check_mode }}"
            and not task.get("register")
        ):
            return True

        return False


if "pytest" in sys.modules:
    import pytest

    IGNORE_ERRORS_TRUE = '''
- hosts: all
  tasks:
    - name: run apt-get update
      command: apt-get update
      ignore_errors: true
'''

    IGNORE_ERRORS_FALSE = '''
- hosts: all
  tasks:
    - name: run apt-get update
      command: apt-get update
      ignore_errors: false
'''

    IGNORE_ERRORS_CHECK_MODE = '''
- hosts: all
  tasks:
    - name: run apt-get update
      command: apt-get update
      ignore_errors: "{{ ansible_check_mode }}"
'''

    IGNORE_ERRORS_REGISTER = '''
- hosts: all
  tasks:
    - name: run apt-get update
      command: apt-get update
      ignore_errors: true
      register: ignore_errors_register
'''

    FAILED_WHEN = '''
- hosts: all
  tasks:
    - name: disable apport
      become: 'yes'
      lineinfile:
        line: "enabled=0"
        dest: /etc/default/apport
        mode: 0644
        state: present
      register: default_apport
      failed_when: default_apport.rc !=0 and not default_apport.rc == 257
'''

    @pytest.mark.parametrize(
        'rule_runner', (IgnoreErrorsRule,), indirect=['rule_runner']
    )
    def test_ignore_errors_true(rule_runner: RunFromText) -> None:
        """The task uses ignore_errors."""
        results = rule_runner.run_playbook(IGNORE_ERRORS_TRUE)
        assert len(results) == 1

    @pytest.mark.parametrize(
        'rule_runner', (IgnoreErrorsRule,), indirect=['rule_runner']
    )
    def test_ignore_errors_false(rule_runner: RunFromText) -> None:
        """The task uses ignore_errors: false, oddly enough."""
        results = rule_runner.run_playbook(IGNORE_ERRORS_FALSE)
        assert len(results) == 0

    @pytest.mark.parametrize(
        'rule_runner', (IgnoreErrorsRule,), indirect=['rule_runner']
    )
    def test_ignore_errors_check_mode(rule_runner: RunFromText) -> None:
        """The task uses ignore_errors: "{{ ansible_check_mode }}"."""
        results = rule_runner.run_playbook(IGNORE_ERRORS_CHECK_MODE)
        print(results)
        assert len(results) == 0

    @pytest.mark.parametrize(
        'rule_runner', (IgnoreErrorsRule,), indirect=['rule_runner']
    )
    def test_ignore_errors_register(rule_runner: RunFromText) -> None:
        """The task uses ignore_errors: but output is registered and managed."""
        results = rule_runner.run_playbook(IGNORE_ERRORS_REGISTER)
        assert len(results) == 0

    @pytest.mark.parametrize(
        'rule_runner', (IgnoreErrorsRule,), indirect=['rule_runner']
    )
    def test_failed_when(rule_runner: RunFromText) -> None:
        """Instead of ignore_errors, this task uses failed_when."""
        results = rule_runner.run_playbook(FAILED_WHEN)
        assert len(results) == 0
