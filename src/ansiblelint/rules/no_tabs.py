"""Implementation of no-tabs rule."""
# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project
from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.yaml_utils import nested_items_path

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable


class NoTabsRule(AnsibleLintRule):
    """Most files should not contain tabs."""

    id = "no-tabs"
    description = "Tabs can cause unexpected display issues, use spaces"
    severity = "LOW"
    tags = ["formatting"]
    version_added = "v4.0.0"
    allow_list = [
        ("lineinfile", "insertafter"),
        ("lineinfile", "insertbefore"),
        ("lineinfile", "regexp"),
        ("lineinfile", "line"),
    ]

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> bool | str:
        for k, v, parent_path in nested_items_path(task):
            if isinstance(k, str) and "\t" in k:
                return True
            parent_key = "" if not parent_path else parent_path[-1]
            if (
                (parent_key, k) not in self.allow_list
                and isinstance(v, str)
                and "\t" in v
            ):
                return True
        return False


RULE_EXAMPLE = r"""---
- hosts: localhost
  tasks:
    - name: Should not trigger no-tabs rules
      lineinfile:
        path: some.txt
        regexp: '^\t$'
        line: 'string with \t inside'
    - name: Foo
      debug:
        msg: "Presence of \t should trigger no-tabs here."
"""

# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:

    import pytest

    @pytest.mark.parametrize("rule_runner", (NoTabsRule,), indirect=["rule_runner"])
    def test_no_tabs_rule(rule_runner: Any) -> None:
        """Test rule matches."""
        results = rule_runner.run_playbook(RULE_EXAMPLE)
        assert results[0].linenumber == 9
        assert results[0].message == NoTabsRule().shortdesc
        assert len(results) == 1
