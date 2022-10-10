"""Implementation of meta-incorrect rule."""
# Copyright (c) 2018, Ansible Project
from __future__ import annotations

from typing import TYPE_CHECKING

from ansiblelint.constants import LINE_NUMBER_KEY, SKIPPED_RULES_KEY
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from typing import Any

    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable


class MetaChangeFromDefaultRule(AnsibleLintRule):
    """meta/main.yml default values should be changed."""

    id = "meta-incorrect"
    field_defaults = [
        ("author", "your name"),
        ("description", "your description"),
        ("company", "your company (optional)"),
        ("license", "license (GPLv2, CC-BY, etc)"),
        ("license", "license (GPL-2.0-or-later, MIT, etc)"),
    ]
    values = ", ".join(sorted({f[0] for f in field_defaults}))
    description = (
        f"You should set appropriate values in meta/main.yml for these fields: {values}"
    )
    severity = "HIGH"
    tags = ["metadata"]
    version_added = "v4.0.0"

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        if file.kind != "meta" or not file.data:
            return []

        galaxy_info = file.data.get("galaxy_info", None)
        if not galaxy_info:
            return []

        results = []
        for field, default in self.field_defaults:
            value = galaxy_info.get(field, None)
            if value and value == default:
                if "meta-incorrect" in file.data.get(SKIPPED_RULES_KEY, []):
                    continue
                results.append(
                    self.create_matcherror(
                        filename=file,
                        linenumber=file.data[LINE_NUMBER_KEY],
                        message=f"Should change default metadata: {field}",
                    )
                )

        return results
