from re import A
import sys

from collections import OrderedDict as odict
from pprint import pp, pprint
from typing import Any, Dict, Union

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.testing import RunFromText
from ansiblelint.file_utils import Lintable

from typing import Optional

# _logger = logging.getLogger(__name__)
# logging.basicConfig(filename='example.log', level=logging.DEBUG)

# skipped rules causes error
# delegate_to is always present
# tags is never in the right order
removed_attributes = ['skipped_rules', 'delegate_to', 'tags']
possible_attrs = [
    "name",
    "when",
    "notify",
    "any_errors_fatal",
    "async",
    "become",
    "become_exe",
    "become_flags",
    "become_method",
    "become_user",
    "remote_user",
    "changed_when",
    "failed_when",
    "check_mode",
    "collections",
    "connection",
    "debugger",
    "delay",
    "delegate_facts",
    "delegate_to",
    "diff",
    "environment",
    "ignore_errors",
    "ignore_unreachable",
    "local_action",
    "module_defaults",
    "no_log",
    "poll",
    "port",
    "timeout",
    "retries",
    "until",
    "register",
    "run_once",
    "throttle",
    "action",
    "args",
    "loop_control",
    "loop",
    "vars",
    "tags",
    # "with_",
]
ordered_expected_attrs = odict(
    (key, idx) for idx, key in enumerate(possible_attrs)
)


class TaskAttributesOrderRule(AnsibleLintRule):
    id = 'attribute-order'
    shortdesc = 'All task attributes should be in order'
    description = 'Task attributes should be in the same order across all lintables'
    severity = 'LOW'
    tags = ['opt-in', 'formatting', 'experimental']
    version_added = 'v5.2.2'
    needs_raw_task = True


    def matchtask(
        self, task: Dict[str, Any], file: 'Optional[Lintable]' = None
    ) -> Union[bool, str]:
        raw_task = task["__raw_task__"]

        # remove skipped attributes from the list
        attrs = []
        for k in raw_task.keys():
            if not k.startswith('__') and (k not in removed_attributes):
                attrs.append(k)

        # get the expected order in from the lookup table
        actual_attrs = odict()
        for attr in attrs:
            pos = ordered_expected_attrs.get(attr)
            if pos == None:
                pos = ordered_expected_attrs.get('action')
            actual_attrs[attr] = pos

        sorted_actual_attrs = odict(
            sorted(actual_attrs.items(), key=lambda item: item[1])
        )

        pprint(actual_attrs)
        pprint(sorted_actual_attrs)
        print(sorted_actual_attrs != actual_attrs)

        # if sorted_actual_attrs != actual_attrs:
        #     return "Please verify the order of the attributes in this task."
        # return False
        return sorted_actual_attrs != actual_attrs


# testing code to be loaded only with pytest or when executed the rule file
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
        assert len(results) == 1
