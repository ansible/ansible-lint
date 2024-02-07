"""Implementation of meta-incorrect rule."""

# Copyright (c) 2018, Ansible Project
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from ansiblelint.constants import LINE_NUMBER_KEY
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
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
                results.append(
                    self.create_matcherror(
                        filename=file,
                        lineno=file.data[LINE_NUMBER_KEY],
                        message=f"Should change default metadata: {field}",
                    ),
                )

        return results


if "pytest" in sys.modules:
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    def test_default_galaxy_info(
        default_rules_collection: RulesCollection,
    ) -> None:
        """Test for meta-incorrect."""
        results = Runner(
            "examples/roles/meta_incorrect_fail",
            rules=default_rules_collection,
        ).run()
        for result in results:
            assert result.rule.id == "meta-incorrect"
        assert len(results) == 4

        assert "Should change default metadata: author" in str(results)
        assert "Should change default metadata: description" in str(results)
        assert "Should change default metadata: company" in str(results)
        assert "Should change default metadata: license" in str(results)
