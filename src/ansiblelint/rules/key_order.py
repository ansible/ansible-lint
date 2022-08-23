"""All tasks should be have name come first."""
from __future__ import annotations

import sys
from typing import Any

from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.testing import RunFromText


class KeyOrderRule(AnsibleLintRule):
    """Ensure specific order of keys in mappings."""

    id = "key-order"
    shortdesc = __doc__
    severity = "LOW"
    tags = ["formatting", "experimental"]
    version_added = "v6.2.0"
    needs_raw_task = True

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> bool | str:
        raw_task = task["__raw_task__"]
        if "name" in raw_task:
            attribute_list = [*raw_task]
            if bool(attribute_list[0] != "name"):
                return "'name' key is not first"
        return False


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:

    import pytest

    PLAY_FAIL = """---
- hosts: localhost
  tasks:
    - no_log: true
      shell: echo hello
      name: Task with no_log on top
    - when: true
      name: Task with when on top
      shell: echo hello
    - delegate_to: localhost
      name: Delegate_to on top
      shell: echo hello
    - loop:
        - 1
        - 2
      name: Loopy
      command: echo {{ item }}
    - become: true
      name: Become first
      shell: echo hello
    - register: test
      shell: echo hello
      name: Register first
"""

    PLAY_SUCCESS = """---
- hosts: localhost
  tasks:
    - name: Test
      command: echo "test"
    - name: Test2
      debug:
        msg: "Debug without a name"
    - name: Flush handlers
      meta: flush_handlers
    - no_log: true  # noqa key-order
      shell: echo hello
      name: Task with no_log on top
"""

    @pytest.mark.parametrize("rule_runner", (KeyOrderRule,), indirect=["rule_runner"])
    def test_task_name_has_name_first_rule_pass(rule_runner: RunFromText) -> None:
        """Test rule matches."""
        results = rule_runner.run_playbook(PLAY_SUCCESS)
        assert len(results) == 0

    @pytest.mark.parametrize("rule_runner", (KeyOrderRule,), indirect=["rule_runner"])
    def test_task_name_has_name_first_rule_fail(rule_runner: RunFromText) -> None:
        """Test rule matches."""
        results = rule_runner.run_playbook(PLAY_FAIL)
        assert len(results) == 6
