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
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task


class NoTabsRule(AnsibleLintRule):
    """Most files should not contain tabs."""

    id = "no-tabs"
    description = "Tabs can cause unexpected display issues, use spaces"
    severity = "LOW"
    tags = ["formatting"]
    version_changed = "4.0.0"
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
    ) -> list[MatchError]:
        result = []
        action = task["action"]["__ansible_module__"]
        for k, v, _ in nested_items_path(task):
            if isinstance(k, str) and "\t" in k and not has_jinja(k):
                result.append(
                    self.create_matcherror(
                        message=self.shortdesc,
                        data=k,
                        filename=file,
                    )
                )
            if (
                isinstance(v, str)
                and "\t" in v
                and (action, k) not in self.allow_list
                and not has_jinja(v)
            ):
                result.append(
                    self.create_matcherror(
                        message=self.shortdesc,
                        data=v,
                        filename=file,
                    )
                )
        return result


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    import pytest

    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    @pytest.mark.libyaml
    def test_no_tabs_rule(default_rules_collection: RulesCollection) -> None:
        """Test rule matches."""
        results = Runner(
            "examples/playbooks/rule-no-tabs.yml",
            rules=default_rules_collection,
        ).run()
        lines = []
        for result in results:
            assert result.rule.id == "no-tabs"
            lines.append(result.lineno)
        assert lines
        # 2.19 has more precise line:columns numbers so the effective result
        # is different.
        assert lines == [10, 13] or lines == [12, 15, 15], lines
