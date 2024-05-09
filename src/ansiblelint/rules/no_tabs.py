"""Implementation of no-tabs rule."""

# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.text import has_jinja
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
        ("win_lineinfile", "insertafter"),
        ("win_lineinfile", "insertbefore"),
        ("win_lineinfile", "regexp"),
        ("win_lineinfile", "line"),
        ("ansible.builtin.lineinfile", "insertafter"),
        ("ansible.builtin.lineinfile", "insertbefore"),
        ("ansible.builtin.lineinfile", "regexp"),
        ("ansible.builtin.lineinfile", "line"),
        ("ansible.legacy.lineinfile", "insertafter"),
        ("ansible.legacy.lineinfile", "insertbefore"),
        ("ansible.legacy.lineinfile", "regexp"),
        ("ansible.legacy.lineinfile", "line"),
        ("community.windows.win_lineinfile", "insertafter"),
        ("community.windows.win_lineinfile", "insertbefore"),
        ("community.windows.win_lineinfile", "regexp"),
        ("community.windows.win_lineinfile", "line"),
    ]

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> bool | str:
        action = task["action"]["__ansible_module__"]
        for k, v, _ in nested_items_path(task):
            if isinstance(k, str) and "\t" in k and not has_jinja(k):
                return True
            if (
                isinstance(v, str)
                and "\t" in v
                and (action, k) not in self.allow_list
                and not has_jinja(v)
            ):
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
        expected_results = [
            (10, NoTabsRule().shortdesc),
            (13, NoTabsRule().shortdesc),
        ]
        for i, expected in enumerate(expected_results):
            assert len(results) >= i + 1
            assert results[i].lineno == expected[0]
            assert results[i].message == expected[1]
        assert len(results) == len(expected), results
