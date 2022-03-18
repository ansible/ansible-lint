"""Implementation of meta-incorrect rule."""
# Copyright (c) 2018, Ansible Project

from typing import TYPE_CHECKING, List

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.utils import LINE_NUMBER_KEY

if TYPE_CHECKING:
    from typing import Any

    from ansiblelint.constants import odict
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
    values = ", ".join(sorted(set((f[0] for f in field_defaults))))
    description = f"meta/main.yml default values should be changed for: {values}"
    severity = "HIGH"
    tags = ["metadata"]
    version_added = "v4.0.0"

    def matchplay(
        self, file: "Lintable", data: "odict[str, Any]"
    ) -> List["MatchError"]:
        if file.kind != "meta":
            return []

        galaxy_info = data.get("galaxy_info", None)
        if not galaxy_info:
            return []

        results = []
        for field, default in self.field_defaults:
            value = galaxy_info.get(field, None)
            if value and value == default:
                results.append(
                    self.create_matcherror(
                        filename=file,
                        linenumber=data[LINE_NUMBER_KEY],
                        message=f"Should change default metadata: {field}",
                    )
                )

        return results
