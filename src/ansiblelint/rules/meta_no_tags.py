"""Implementation of meta-no-tags rule."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from ansiblelint.rules import AnsibleLintRule

# Copyright (c) 2018, Ansible Project


if TYPE_CHECKING:
    from typing import Any

    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable
    from ansiblelint.testing import RunFromText


class MetaTagValidRule(AnsibleLintRule):
    """Tags must contain lowercase letters and digits only."""

    id = "meta-no-tags"
    description = (
        "Tags must contain lowercase letters and digits only, "
        "and ``galaxy_tags`` is expected to be a list"
    )
    severity = "HIGH"
    tags = ["metadata"]
    version_added = "v4.0.0"

    TAG_REGEXP = re.compile("^[a-z0-9]+$")

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        """Find violations inside meta files."""
        if file.kind != "meta" or not file.data:
            return []

        galaxy_info = file.data.get("galaxy_info", None)
        if not galaxy_info:
            return []

        tags = []
        results = []

        if "galaxy_tags" in galaxy_info:
            if isinstance(galaxy_info["galaxy_tags"], list):
                tags += galaxy_info["galaxy_tags"]
            else:
                results.append(
                    self.create_matcherror(
                        "Expected 'galaxy_tags' to be a list",
                        filename=file,
                    ),
                )

        if "categories" in galaxy_info:
            results.append(
                self.create_matcherror(
                    "Use 'galaxy_tags' rather than 'categories'",
                    filename=file,
                ),
            )
            if isinstance(galaxy_info["categories"], list):
                tags += galaxy_info["categories"]
            else:
                results.append(
                    self.create_matcherror(
                        "Expected 'categories' to be a list",
                        filename=file,
                    ),
                )

        for tag in tags:
            msg = self.shortdesc
            if not isinstance(tag, str):
                results.append(
                    self.create_matcherror(
                        f"Tags must be strings: '{tag}'",
                        filename=file,
                    ),
                )
                continue
            if not re.match(self.TAG_REGEXP, tag):
                results.append(
                    self.create_matcherror(
                        message=f"{msg}, invalid: '{tag}'",
                        filename=file,
                    ),
                )

        return results


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    import pytest

    @pytest.mark.parametrize(
        "rule_runner",
        (MetaTagValidRule,),
        indirect=["rule_runner"],
    )
    def test_valid_tag_rule(rule_runner: RunFromText) -> None:
        """Test rule matches."""
        results = rule_runner.run(
            Path("examples/roles/meta_no_tags_valid/meta/main.yml"),
        )
        assert "Use 'galaxy_tags' rather than 'categories'" in str(results), results
        assert "Expected 'categories' to be a list" in str(results)
        assert "invalid: 'my s q l'" in str(results)
        assert "invalid: 'MYTAG'" in str(results)

    @pytest.mark.parametrize(
        "rule_runner",
        (MetaTagValidRule,),
        indirect=["rule_runner"],
    )
    def test_meta_not_tags(rule_runner: Any) -> None:
        """Test rule matches."""
        results = rule_runner.run(
            "examples/roles/meta_no_tags_galaxy_info/meta/main.yml",
        )
        assert results == []

    @pytest.mark.parametrize(
        "rule_runner",
        (MetaTagValidRule,),
        indirect=["rule_runner"],
    )
    def test_no_galaxy_tags_list(rule_runner: Any) -> None:
        """Test rule matches."""
        results = rule_runner.run("examples/roles/meta_tags_no_list/meta/main.yml")
        assert "Expected 'galaxy_tags' to be a list" in str(results)

    @pytest.mark.parametrize(
        "rule_runner",
        (MetaTagValidRule,),
        indirect=["rule_runner"],
    )
    def test_galaxy_categories_as_list(rule_runner: Any) -> None:
        """Test rule matches."""
        results = rule_runner.run(
            "examples/roles/meta_categories_as_list/meta/main.yml",
        )
        assert "Use 'galaxy_tags' rather than 'categories'" in str(results), results
        assert "Expected 'categories' to be a list" not in str(results)

    @pytest.mark.parametrize(
        "rule_runner",
        (MetaTagValidRule,),
        indirect=["rule_runner"],
    )
    def test_tags_not_a_string(rule_runner: Any) -> None:
        """Test rule matches."""
        results = rule_runner.run("examples/roles/meta_tags_not_a_string/meta/main.yml")
        assert "Tags must be strings" in str(results)
