"""Implementation of meta-runtime rule."""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from galaxy import Version

from ansiblelint.rules import AnsibleLintRule

# Copyright (c) 2023, Ansible Project


if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable


class ChangelogGalaxyVersion(AnsibleLintRule):
    """Required latest changlog version should be in sync with the version in galaxy.yml"""

    id = "changelog-galaxy-version"
    description = (
        "The latest changlog version should be in sync with the version in galaxy.yml"
    )
    severity = "VERY_HIGH"
    tags = ["metadata"]
    version_added = "v6.11.0 (last update)"

    _ids = {
        "changelog-galaxy-version[update-version]": "latest changelog version should be in sync with version in galaxy.yml",
    }

    def matchyaml(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        """Find violations inside meta files.

        :param file: Input lintable file that is a match for `meta-runtime`
        :returns: List of errors matched to the input file
        """
        results = []

        if file.kind != "changelog":  # type: ignore[comparison-overlap]
            return []

        release_data = file.data.get("releases", None)
        version_required = data.get("releases", None)

        version = data.get("version")
        if Version(version) < Version("1.0.0"):
            results.append(
                self.create_matcherror(
                    message="collection version should be greater than or equal to 1.0.0",
                    lineno=version._line_number,  # noqa: SLF001
                    tag="galaxy[version-incorrect]",
                    filename=file,
                ),
            )

        return results


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    import pytest

    # pylint: disable=ungrouped-imports
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    @pytest.mark.parametrize(
        ("test_file", "failures", "tags"),
        (
            pytest.param(
                "examples/meta_runtime_version_checks/pass/meta/runtime.yml",
                0,
                "meta-runtime[unsupported-version]",
                id="pass",
            ),
            pytest.param(
                "examples/meta_runtime_version_checks/fail_0/meta/runtime.yml",
                1,
                "meta-runtime[unsupported-version]",
                id="fail0",
            ),
            pytest.param(
                "examples/meta_runtime_version_checks/fail_1/meta/runtime.yml",
                1,
                "meta-runtime[unsupported-version]",
                id="fail1",
            ),
            pytest.param(
                "examples/meta_runtime_version_checks/fail_2/meta/runtime.yml",
                1,
                "meta-runtime[invalid-version]",
                id="fail2",
            ),
        ),
    )
    def test_meta_supported_version(
        default_rules_collection: RulesCollection,
        test_file: str,
        failures: int,
        tags: str,
    ) -> None:
        """Test rule matches."""
        default_rules_collection.register(ChangelogGalaxyVersion())
        results = Runner(test_file, rules=default_rules_collection).run()
        for result in results:
            assert result.rule.id == ChangelogGalaxyVersion().id
            assert result.tag == tags
        assert len(results) == failures
