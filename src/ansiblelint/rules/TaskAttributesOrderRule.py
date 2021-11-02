import logging
import sys
from collections import OrderedDict as odict
from pprint import pp, pprint
from typing import TYPE_CHECKING, Any, Dict, Union

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.testing import RunFromText

if TYPE_CHECKING:
    from typing import Optional

    from ansiblelint.file_utils import Lintable

# skipped rules causes error
# delegate_to is always present
# tags is never in the right order
removed_attributes = ['skipped_rules', 'delegate_to', 'tags']
possible_attrs = [
    "name",
    "any_errors_fatal",
    "async",
    "become",
    "become_exe",
    "become_flags",
    "become_method",
    "become_user",
    "changed_when",
    "check_mode",
    "collections",
    "connection",
    "debugger",
    "delay",
    "delegate_facts",
    "delegate_to",
    "diff",
    "environment",
    "failed_when",
    "ignore_errors",
    "ignore_unreachable",
    "local_action",
    "module_defaults",
    "no_log",
    "poll",
    "port",
    "register",
    "remote_user",
    "retries",
    "run_once",
    "throttle",
    "timeout",
    "until",
    "vars",
    "when",
    "action",
    "args",
    "notify",
    "loop",
    "loop_control",
    "tags",
    # "with_",
]
ordered_expected_attrs = odict((key, idx) for idx, key in enumerate(possible_attrs))

# _logger = logging.getLogger(__name__)
# logging.basicConfig(filename='example.log', level=logging.DEBUG)


class TaskAttributesOrderRule(AnsibleLintRule):
    id = 'attribute-order'
    shortdesc = 'All task attributes should be in order'
    description = 'Task attributes should be in the same order across all lintables'
    severity = 'LOW'
    tags = ['opt-in', 'formatting', 'experimental']
    version_added = 'v5.2.2'

    def matchtask(
        self, task: Dict[str, Any], file: 'Optional[Lintable]' = None
    ) -> Union[bool, str]:
        attrs = []
        for k in task.keys():
            if not k.startswith('__') and (k not in removed_attributes):
                attrs.append(k)

        actual_attrs = odict()
        for attr in attrs:
            actual_attrs[attr] = ordered_expected_attrs[attr]

        sorted_actual_attrs = odict(
            sorted(actual_attrs.items(), key=lambda item: item[1])
        )

        # logging.info(('actual:', actual_attrs))
        # logging.info(('sorted:', sorted_actual_attrs))
        # logging.info(sorted_actual_attrs != actual_attrs)

        return sorted_actual_attrs != actual_attrs


if "pytest" in sys.modules:
    import pytest

    PLAY_FAIL = """---
- hosts: localhost
  tasks:
    - shell: echo hello
      name: task with name on bottom
      when: true
"""

    PLAY_SUCCESS = """---
- hosts: localhost
  tasks:
    - name: task with when on top
      when: true
      shell: echo hello
    - shell: echo hello
    - delegate_to: localhost
      shell: echo hello
    - shell: echo hello
      name: test
"""

    @pytest.mark.parametrize(
        'rule_runner', (TaskAttributesOrderRule,), indirect=['rule_runner']
    )
    def test_task_attribute_order_rule_pass(rule_runner: RunFromText) -> None:
        """The task has when second."""
        results = rule_runner.run_playbook(PLAY_SUCCESS)
        assert len(results) == 0

    @pytest.mark.parametrize(
        'rule_runner', (TaskAttributesOrderRule,), indirect=['rule_runner']
    )
    def test_task_attribute_order_rule_fail(rule_runner: RunFromText) -> None:
        """The task has when last."""
        results = rule_runner.run_playbook(PLAY_FAIL)
        pprint(results)
        assert len(results) == 1
