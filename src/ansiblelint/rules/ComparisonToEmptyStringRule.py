# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project

import re
import sys
from typing import TYPE_CHECKING, Any, Dict, Union

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.testing import RunFromText
from ansiblelint.utils import nested_items

if TYPE_CHECKING:
    from typing import Optional

    from ansiblelint.file_utils import Lintable


class ComparisonToEmptyStringRule(AnsibleLintRule):
    id = 'empty-string-compare'
    shortdesc = "Don't compare to empty string"
    description = (
        'Use ``when: var|length > 0`` rather than ``when: var != ""`` (or '
        'conversely ``when: var|length == 0`` rather than ``when: var == ""``)'
    )
    severity = 'HIGH'
    tags = ['idiom']
    version_added = 'v4.0.0'

    empty_string_compare = re.compile("[=!]= ?(\"{2}|'{2})")

    def matchtask(
        self, task: Dict[str, Any], file: 'Optional[Lintable]' = None
    ) -> Union[bool, str]:
        for k, v, _ in nested_items(task):
            if k == 'when':
                if isinstance(v, str):
                    if self.empty_string_compare.search(v):
                        return True
                elif isinstance(v, bool):
                    pass
                else:
                    for item in v:
                        if isinstance(item, str) and self.empty_string_compare.search(
                            item
                        ):
                            return True

        return False


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:

    import pytest

    SUCCESS_PLAY = '''
- hosts: all
  tasks:
    - name: shut down
      shell: |
        /sbin/shutdown -t now
        echo $var == ""
      when: ansible_os_family
'''

    FAIL_PLAY = '''
- hosts: all
  tasks:
  - name: shut down
    command: /sbin/shutdown -t now
    when: ansible_os_family == ""
  - name: shut down
    command: /sbin/shutdown -t now
    when: ansible_os_family !=""
'''

    @pytest.mark.parametrize(
        'rule_runner', (ComparisonToEmptyStringRule,), indirect=['rule_runner']
    )
    def test_rule_empty_string_compare_fail(rule_runner: RunFromText) -> None:
        """Test rule matches."""
        results = rule_runner.run_playbook(FAIL_PLAY)
        assert len(results) == 2
        for result in results:
            assert result.message == ComparisonToEmptyStringRule.shortdesc

    @pytest.mark.parametrize(
        'rule_runner', (ComparisonToEmptyStringRule,), indirect=['rule_runner']
    )
    def test_rule_empty_string_compare_pass(rule_runner: RunFromText) -> None:
        """Test rule matches."""
        results = rule_runner.run_playbook(SUCCESS_PLAY)
        assert len(results) == 0, results
