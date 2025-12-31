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
        # Check the key/value pairs found by the nested pathing
        for k, v, _path in nested_items_path(task):
            # Check if the Key itself has a tab (almost never allowed)
            if isinstance(k, str) and "\t" in k and not has_jinja(k):
                result.append(
                    self.create_matcherror(
                        message=self.shortdesc,
                        data=k,
                        filename=file,
                    )
                )

            # Check if the Value has a tab
            if isinstance(v, str) and "\t" in v and not has_jinja(v):
                # We check if 'k' is in our allow_list for ANY of the modules
                is_allowed = any(k == allowed_key for _, allowed_key in self.allow_list)

                if not is_allowed:
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

    @pytest.mark.libyaml
    def test_no_tabs_block_pass(default_rules_collection: RulesCollection) -> None:
        """Verify that tabs are allowed in lineinfile even inside blocks."""
        results = Runner(
            "examples/playbooks/rule-no-tabs-block-pass.yml",
            rules=default_rules_collection,
        ).run()
        assert len(results) == 0
