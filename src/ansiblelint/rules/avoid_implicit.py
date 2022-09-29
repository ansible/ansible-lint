"""Implementation of avoid-implicit rule."""
# https://github.com/ansible/ansible-lint/issues/2501
from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable


class AvoidImplicitRule(AnsibleLintRule):
    """Rule that identifies use of undocumented or discouraged implicit behaviors."""

    id = "avoid-implicit"
    shortdesc = "Avoid implicit behaviors"
    description = (
        "Items which are templated should use ``template`` instead of "
        "``copy`` with ``content`` to ensure correctness."
    )
    severity = "MEDIUM"
    tags = ["unpredictability", "experimental"]
    version_added = "v6.8.0"

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> bool | str:
        """Confirm if current rule is matching a specific task."""
        if task["action"]["__ansible_module__"] == "copy":
            content = task["action"].get("content", "")
            if not isinstance(content, str):
                return True
        return False


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:

    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.runner import Runner  # pylint: disable=ungrouped-imports

    def test_template_instead_of_copy_positive() -> None:
        """Positive test for avoid-implicit."""
        collection = RulesCollection()
        collection.register(AvoidImplicitRule())
        success = "examples/playbooks/rule-avoid-implicit-pass.yml"
        good_runner = Runner(success, rules=collection)
        assert [] == good_runner.run()

    def test_template_instead_of_copy_negative() -> None:
        """Negative test for avoid-implicit."""
        collection = RulesCollection()
        collection.register(AvoidImplicitRule())
        failure = "examples/playbooks/rule-avoid-implicit-fail.yml"
        bad_runner = Runner(failure, rules=collection)
        errs = bad_runner.run()
        assert len(errs) == 1
