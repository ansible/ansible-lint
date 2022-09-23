"""Implementation of the literal-compare rule."""
# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018-2021, Ansible Project

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.yaml_utils import nested_items_path

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable


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
        self, task: dict[str, Any], file: Lintable | None = None
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
                            item
                        ):
                            return True

        return False
