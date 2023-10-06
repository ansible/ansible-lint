"""Implementation of no-tabs rule."""
# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.yaml_utils import nested_items_path

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task


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
        ("ansible.builtin.lineinfile", "insertafter"),
        ("ansible.builtin.lineinfile", "insertbefore"),
        ("ansible.builtin.lineinfile", "regexp"),
        ("ansible.builtin.lineinfile", "line"),
        ("ansible.legacy.lineinfile", "insertafter"),
        ("ansible.legacy.lineinfile", "insertbefore"),
        ("ansible.legacy.lineinfile", "regexp"),
        ("ansible.legacy.lineinfile", "line"),
    ]

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> bool | str:
        action = task["action"]["__ansible_module__"]
        for k, v, _ in nested_items_path(task):
            if isinstance(k, str) and "\t" in k:
                return True
            if isinstance(v, str) and "\t" in v and (action, k) not in self.allow_list:
                return True
        return False


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    def test_no_tabs_rule(default_rules_collection: RulesCollection) -> None:
        """Test rule matches."""
        results = Runner(
            "examples/playbooks/rule-no-tabs.yml",
            rules=default_rules_collection,
        ).run()
        assert results[0].lineno == 10
        assert results[0].message == NoTabsRule().shortdesc
        assert len(results) == 2
