"""Implementation of template-instead-of-copy rule."""
# cspell:disable-next-line
# Copyright (c) 2022, Alexander Skiba
# references
# - github discussion of issue: https://github.com/ansible/ansible/issues/50580
# - ansible docs with warning: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/copy_module.html#synopsis
from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable


class UseTemplateInsteadOfCopyRule(AnsibleLintRule):
    """Rule that identifies improper use copy instead of template."""

    id = "template-instead-of-copy"
    shortdesc = "Templated files should use template instead of copy"
    description = (
        "Items which are templated should use ``template`` instead of "
        "``copy`` with ``content`` to ensure correctness."
    )
    severity = "MEDIUM"
    tags = ["unpredictability"]
    version_added = "custom"

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> bool | str:
        """Confirm if current rule is matching a specific task."""
        if task["action"]["__ansible_module__"] == "copy":
            content = task["action"].get("content", "")
            if "{{" in content:
                return True
        return False


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:

    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.runner import Runner  # pylint: disable=ungrouped-imports

    def test_template_instead_of_copy_positive() -> None:
        """Positive test for partial-become."""
        collection = RulesCollection()
        collection.register(UseTemplateInsteadOfCopyRule())
        success = "examples/playbooks/rule-template-instead-of-copy-success.yml"
        good_runner = Runner(success, rules=collection)
        assert [] == good_runner.run()

    def test_template_instead_of_copy_negative() -> None:
        """Negative test for partial-become."""
        collection = RulesCollection()
        collection.register(UseTemplateInsteadOfCopyRule())
        failure = "examples/playbooks/rule-template-instead-of-copy-failure.yml"
        bad_runner = Runner(failure, rules=collection)
        errs = bad_runner.run()
        assert len(errs) == 1
