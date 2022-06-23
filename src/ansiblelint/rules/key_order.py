"""All tasks should be have name come first."""
import sys
from collections import OrderedDict as odict
from typing import Any, Dict, Optional, Union

from ansiblelint.config import options
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.testing import RunFromText


class KeyOrderRule(AnsibleLintRule):
    """Ensure specific order of keys in mappings."""

    id = "key-order"
    description = """\
Keys should be in the specified order. In the default configuration, it only enforces name first. Checking the order of all keys can be anabled by setting 'key_order' in the config
"""
    shortdesc = __doc__
    severity = "LOW"
    tags = ["formatting", "experimental"]
    version_added = "v6.2.0"
    needs_raw_task = True

    # skipped rules is not a key
    removed_keys = ["skipped_rules"]
    possible_keys = options.key_order
    if options.custom_key_order:
        possible_keys = options.custom_key_order

    ordered_expected_keys = odict((key, idx) for idx, key in enumerate(possible_keys))

    def matchtask(
        self, task: Dict[str, Any], file: Optional[Lintable] = None
    ) -> Union[bool, str]:
        keys = task["__raw_task__"].keys()

        # get the expected order in from the lookup table
        actual_order = odict()
        for attr in keys:
            if not attr.startswith("__") and (attr not in self.removed_keys):
                pos = self.ordered_expected_keys.get(attr)
                if pos == None:
                    pos = self.ordered_expected_keys.get("action")
                actual_order[attr] = pos

        sorted_actual_order = odict(
            sorted(actual_order.items(), key=lambda item: item[1])
        )

        if bool(sorted_actual_order != actual_order):
            text = ",".join(sorted_actual_order.keys())
            return f"Keys are not in order. Expected order '{text}'"
        return False


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
    - tags: hello
      no_log: true
      name: echo hello with tags
      become: true
      delegate_to: localhost
      shell: echo hello with tags
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
    - name: task with no_log on top
      no_log: true  # noqa key-order
      shell: echo hello
    - name: echo hello with tags
      become: true
      delegate_to: localhost
      no_log: true
      shell: echo hello with tags
      tags: hello
    - name: loopy
      command: echo {{ item }}
      loop:
        - 1
        - 2
    - no_log: true  # noqa key-order
      shell: echo hello
      name: task with no_log on top
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
        assert len(results) == 7
