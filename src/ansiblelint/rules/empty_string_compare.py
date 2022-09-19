"""Implementation of empty-string-compare rule."""
# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project

from __future__ import annotations

import re
import sys
from typing import TYPE_CHECKING, Any

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.yaml_utils import nested_items_path

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable


class ComparisonToEmptyStringRule(AnsibleLintRule):
    """Don't compare to empty string."""

    id = "empty-string-compare"
    description = (
        'Use ``when: var|length > 0`` rather than ``when: var != ""`` (or '
        'conversely ``when: var|length == 0`` rather than ``when: var == ""``)'
    )
    severity = "HIGH"
    tags = ["idiom", "opt-in"]
    version_added = "v4.0.0"

    empty_string_compare = re.compile("[=!]= ?(\"{2}|'{2})")

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> bool | str:
        for k, v, _ in nested_items_path(task):
            if k == "when":
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

    from ansiblelint.testing import RunFromText  # pylint: disable=ungrouped-imports

    SUCCESS_PLAY = """
- hosts: all
  tasks:
    - name: Shut down
      shell: |
        /sbin/shutdown -t now
        echo $var == ""
      when: ansible_os_family
"""

    FAIL_PLAY = """
- hosts: all
  tasks:
  - name: Shut down
    command: /sbin/shutdown -t now
    when: ansible_os_family == ""
  - name: Shut down
    command: /sbin/shutdown -t now
    when: ansible_os_family !=""
"""

    @pytest.mark.parametrize(
        "rule_runner", (ComparisonToEmptyStringRule,), indirect=["rule_runner"]
    )
    def test_rule_empty_string_compare_fail(rule_runner: RunFromText) -> None:
        """Test rule matches."""
        results = rule_runner.run_playbook(FAIL_PLAY)
        assert len(results) == 2
        for result in results:
            assert result.message == ComparisonToEmptyStringRule().shortdesc

    @pytest.mark.parametrize(
        "rule_runner", (ComparisonToEmptyStringRule,), indirect=["rule_runner"]
    )
    def test_rule_empty_string_compare_pass(rule_runner: RunFromText) -> None:
        """Test rule matches."""
        results = rule_runner.run_playbook(SUCCESS_PLAY)
        assert len(results) == 0, results
