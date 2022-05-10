"""All tasks should be have name come first."""
import sys
from typing import Any, Dict, Optional

from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.testing import RunFromText


class TaskHasNameFirstRule(AnsibleLintRule):
    """All tasks should be have name come first."""

    id = "task-name-first"
    shortdesc = __doc__
    severity = "LOW"
    tags = ["formatting", "experimental"]
    version_added = "v6.2.0"
    needs_raw_task = True

    def matchtask(self, task: Dict[str, Any], file: Optional[Lintable] = None) -> bool:
        raw_task = task["__raw_task__"]
        attribute_list = [*raw_task]

        return bool(attribute_list[0] != "name")


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:

    import pytest

    PLAY_FAIL = """---
- hosts: localhost
  tasks:
    - no_log: true
      shell: echo hello
      name: task with no_log on top
    - when: true
      name: task with when on top
      shell: echo hello
    - delegate_to: localhost
      name: delegate_to on top
      shell: echo hello
    - loop:
        - 1
        - 2
      name: loopy
      command: echo {{ item }}
    - become: true
      name: become first
      shell: echo hello
    - register: test
      shell: echo hello
      name: register first
"""

    PLAY_SUCCESS = """---
- hosts: localhost
  tasks:
    - name: test
      command: echo "test"
    - name: test2
      debug:
        msg: "Debug without a name"
    - name: Flush handlers
      meta: flush_handlers
    - no_log: true  # noqa task-name-first
      shell: echo hello
      name: task with no_log on top
"""

    @pytest.mark.parametrize(
        "rule_runner", (TaskHasNameFirstRule,), indirect=["rule_runner"]
    )
    def test_task_name_has_name_first_rule_pass(rule_runner: RunFromText) -> None:
        """Test rule matches."""
        results = rule_runner.run_playbook(PLAY_SUCCESS)
        assert len(results) == 0

    @pytest.mark.parametrize(
        "rule_runner", (TaskHasNameFirstRule,), indirect=["rule_runner"]
    )
    def test_task_name_has_name_first_rule_fail(rule_runner: RunFromText) -> None:
        """Test rule matches."""
        results = rule_runner.run_playbook(PLAY_FAIL)
        assert len(results) == 6
