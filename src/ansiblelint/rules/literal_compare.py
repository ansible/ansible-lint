"""Implementation of the literal-compare rule."""

# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018-2021, Ansible Project

from __future__ import annotations

import re
import sys
from typing import TYPE_CHECKING

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.yaml_utils import nested_items_path

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task


class ComparisonToLiteralBoolRule(AnsibleLintRule):
    """Don't compare to literal True/False."""

    id = "literal-compare"
    description = (
        "Use ``when: var`` rather than ``when: var == True`` "
        "(or conversely ``when: not var``)"
    )
    severity = "HIGH"
    tags = ["idiom"]
    version_added = "v4.0.0"

    literal_bool_compare = re.compile("[=!]= ?(True|true|False|false)")

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> bool | str:
        for k, v, _ in nested_items_path(task):
            if k == "when":
                if isinstance(v, str):
                    if self.literal_bool_compare.search(v):
                        return True
                elif isinstance(v, bool):
                    pass
                else:
                    for item in v:
                        if isinstance(item, str) and self.literal_bool_compare.search(
                            item,
                        ):
                            return True

        return False


if "pytest" in sys.modules:
    import pytest

    # pylint: disable=ungrouped-imports
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    @pytest.mark.parametrize(
        ("test_file", "failures"),
        (
            pytest.param(
                "examples/playbooks/rule_literal_compare_fail.yml",
                3,
                id="fail",
            ),
            pytest.param(
                "examples/playbooks/rule_literal_compare_pass.yml",
                0,
                id="pass",
            ),
        ),
    )
    def test_literal_compare(
        default_rules_collection: RulesCollection,
        test_file: str,
        failures: int,
    ) -> None:
        """Test rule matches."""
        # Enable checking of loop variable prefixes in roles
        results = Runner(test_file, rules=default_rules_collection).run()
        for result in results:
            assert result.rule.id == "literal-compare"
        assert len(results) == failures
