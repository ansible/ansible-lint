"""Rule definition for avoiding internal names for certain collections."""
from __future__ import annotations

import sys
from typing import Any

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule

COLLECTIONS_WITH_FLATMAPPING = [
    "community.general",
    "community.network",
]


class InternalNamesRule(AnsibleLintRule):
    """Avoid internal names for actions."""

    id = "internal_names"
    severity = "VERY_HIGH"
    description = "Check whether actions are using internal names from collections names that should not be used."
    tags = ["formatting"]
    version_added = "v6.9.0"

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> list[MatchError]:
        result: list[MatchError] = []
        module = task["action"]["__ansible_module_original__"]
        parts = module.split(".")
        if len(parts) <= 3:
            return result
        collection = ".".join(parts[:2])
        if collection in COLLECTIONS_WITH_FLATMAPPING:
            if len(parts) > 3:
                result.append(
                    self.create_matcherror(
                        message=f"Do not use internal name for {collection} module actions ({module}).",
                        details=f"Use `{collection}.{parts[-1]}` instead.",
                        filename=file,
                        linenumber=task["__line__"],
                        tag=f"internal_names[{collection}]",
                    )
                )
        return result


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:

    import pytest

    from ansiblelint.testing import RunFromText  # pylint: disable=ungrouped-imports

    SUCCESS_PLAY = """
- hosts: localhost
  tasks:
  - name: Correct name for community.general
    community.general.sudoers:
      name: should-not-be-here
      state: absent
  - name: Correct name for community.network
    community.network.network.edgeos.edgeos_facts:
      gather_subset: all
    """

    FAIL_PLAY = """
- hosts: localhost
  tasks:
  - name: Internal name for community.general (internal_names[community.general])
    community.general.system.sudoers:
      name: should-not-be-here
      state: absent
  - name: Internal name for community.network (internal_names[community.network])
    community.network.edgeos_facts:
      gather_subset: all
    """

    @pytest.mark.parametrize(
        "rule_runner", (InternalNamesRule,), indirect=["rule_runner"]
    )
    def test_internal_names_fail(rule_runner: RunFromText) -> None:
        """Test rule matches."""
        results = rule_runner.run_playbook(FAIL_PLAY)
        assert len(results) == 2
        assert results[0].tag == "internal_names[community.general]"
        assert (
            "Do not use internal names for community.network module actions"
            in results[0].message
        )
        assert results[1].tag == "internal_names[community.network]"
        assert (
            "Do not use internal names for community.general module actions"
            in results[1].message
        )

    @pytest.mark.parametrize(
        "rule_runner", (InternalNamesRule,), indirect=["rule_runner"]
    )
    def test_internal_names_pass(rule_runner: RunFromText) -> None:
        """Test rule does not match."""
        results = rule_runner.run_playbook(SUCCESS_PLAY)
        assert len(results) == 0, results
