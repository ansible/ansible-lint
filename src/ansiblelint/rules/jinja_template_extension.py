"""Implementation of the jinja-template-extension rule."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task


class JinjaTemplateExtensionRule(AnsibleLintRule):
    """Template files should have a .j2 extension."""

    id = "jinja-template-extension"
    description = (
        "Template source files should end in ``.j2`` to clearly distinguish "
        "them from static files and enable proper editor syntax highlighting."
    )
    severity = "LOW"
    tags = ["formatting", "opt-in"]
    version_changed = "6.22.0"

    _template_modules = (
        "ansible.builtin.template",
        "ansible.legacy.template",
        "template",
    )

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> bool | str:
        if task["action"]["__ansible_module__"] not in self._template_modules:
            return False

        src = task["action"].get("src", "")
        if not isinstance(src, str) or not src:
            return False

        if not src.endswith(".j2"):
            return "Template source file should have a .j2 extension"

        return False


if "pytest" in sys.modules:
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    def test_jinja_template_extension_fail(
        empty_rule_collection: RulesCollection,
    ) -> None:
        """Test rule catches template src without .j2 extension."""
        empty_rule_collection.register(JinjaTemplateExtensionRule())
        results = Runner(
            "examples/playbooks/rule-jinja-template-extension-fail.yml",
            rules=empty_rule_collection,
        ).run()
        assert len(results) == 2
        for result in results:
            assert result.rule.id == JinjaTemplateExtensionRule.id

    def test_jinja_template_extension_pass(
        empty_rule_collection: RulesCollection,
    ) -> None:
        """Test rule allows template src with .j2 extension."""
        empty_rule_collection.register(JinjaTemplateExtensionRule())
        results = Runner(
            "examples/playbooks/rule-jinja-template-extension-pass.yml",
            rules=empty_rule_collection,
        ).run()
        assert len(results) == 0, results
