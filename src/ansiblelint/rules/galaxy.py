"""Implementation of GalaxyRule."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from ansiblelint.constants import (
    FILENAME_KEY,
    LINE_NUMBER_KEY,
    MAX_LENGTH_TAG,
    MAX_TAGS_COUNT,
    TAG_NAME_REGEXP,
)
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable


class GalaxyRule(AnsibleLintRule):
    """Rule for checking collections."""

    id = "galaxy"
    description = "Confirm that collection's units are valid."
    severity = "MEDIUM"
    tags = ["metadata"]
    version_changed = "6.11.0"
    _ids = {
        "galaxy[tags]": "galaxy.yaml must have one of the required tags",
        "galaxy[tags-format]": "galaxy.yaml one or more tags are not formatted properly.",
        "galaxy[tags-length]": "galaxy.yaml one or more tags exceed character length.",
        "galaxy[tags-count]": "galaxy.yaml has too many tags.",
        "galaxy[no-changelog]": "No changelog found. Please add a changelog file. Refer to the galaxy.md file for more info.",
        "galaxy[version-missing]": "galaxy.yaml should have version tag.",
        "galaxy[no-runtime]": "meta/runtime.yml file not found.",
        "galaxy[invalid-dependency-version]": "Invalid collection metadata. Dependency version spec range is invalid",
    }

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        """Return matches found for a specific play (entry in playbook)."""
        if file.kind != "galaxy":
            return []

        # Defined by Automation Hub Team and Partner Engineering
        required_tag_list = [
            "application",
            "cloud",
            "database",
            "eda",
            "infrastructure",
            "linux",
            "monitoring",
            "networking",
            "security",
            "storage",
            "tools",
            "windows",
        ]

        results = []

        base_path = file.path.parent.resolve()
        changelog_found = 0
        changelog_paths = [
            base_path / "changelogs" / "changelog.yaml",
            base_path / "changelogs" / "changelog.yml",
            base_path / "CHANGELOG.rst",
            base_path / "CHANGELOG.md",
        ]

        for path in changelog_paths:
            if path.is_file():
                changelog_found = 1
        galaxy_tag_list = data.get("tags", [])
        galaxy_tag_invalid_format = [
            tag for tag in galaxy_tag_list if not TAG_NAME_REGEXP.match(tag)
        ]
        galaxy_tag_invalid_length = [
            tag for tag in galaxy_tag_list if len(tag) > MAX_LENGTH_TAG
        ]

        collection_deps = data.get("dependencies")
        if collection_deps:
            for dep, ver in collection_deps.items():
                if (
                    dep not in [LINE_NUMBER_KEY, FILENAME_KEY]
                    and len(str(ver).strip()) == 0
                ):
                    results.append(
                        self.create_matcherror(
                            message=f"Invalid collection metadata. Dependency version spec range is invalid for '{dep}'.",
                            tag="galaxy[invalid-dependency-version]",
                            filename=file,
                        ),
                    )

        # Changelog Check - building off Galaxy rule as there is no current way to check
        # for a nonexistent file
        if not changelog_found:
            results.append(
                self.create_matcherror(
                    message="No changelog found. Please add a changelog file. Refer to the galaxy.md file for more info.",
                    tag="galaxy[no-changelog]",
                    filename=file,
                ),
            )

        # Checking if galaxy.yml contains one or more required tags for certification
        if not galaxy_tag_list or not any(
            tag in required_tag_list for tag in galaxy_tag_list
        ):
            results.append(
                self.create_matcherror(
                    message=(
                        f"galaxy.yaml must have one of the required tags: {required_tag_list}"
                    ),
                    tag="galaxy[tags]",
                    filename=file,
                ),
            )

        # Checking if galaxy.yml tags are formatted correctly
        if galaxy_tag_invalid_format:
            results.append(
                self.create_matcherror(
                    message=(
                        f"galaxy.yaml must have properly formatted tags. Invalid tags: {','.join(galaxy_tag_invalid_format)}"
                    ),
                    tag="galaxy[tags-format]",
                    filename=file,
                ),
            )

        # Checking if galaxy.yml tags length are within limits
        if galaxy_tag_invalid_length:
            results.append(
                self.create_matcherror(
                    message=(
                        f"galaxy.yaml tags must not exceed {MAX_LENGTH_TAG} characters. Invalid tags: {','.join(galaxy_tag_invalid_length)}"
                    ),
                    tag="galaxy[tags-length]",
                    filename=file,
                ),
            )

        # Checking if galaxy.yml tags does not exceed the max number
        if len(galaxy_tag_list) > MAX_TAGS_COUNT:
            results.append(
                self.create_matcherror(
                    message=(
                        f"galaxy.yaml exceeds {MAX_TAGS_COUNT} tags. Current count: {len(galaxy_tag_list)}"
                    ),
                    tag="galaxy[tags-count]",
                    filename=file,
                ),
            )

        if "version" not in data:
            results.append(
                self.create_matcherror(
                    message="galaxy.yaml should have version tag.",
                    data=data,
                    tag="galaxy[version-missing]",
                    filename=file,
                ),
            )
            return results
            # returning here as it does not make sense
            # to continue for version check below

        if not (base_path / "meta" / "runtime.yml").is_file():
            results.append(
                self.create_matcherror(
                    message="meta/runtime.yml file not found.",
                    tag="galaxy[no-runtime]",
                    filename=file,
                ),
            )

        return results


if "pytest" in sys.modules:
    import pytest

    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.runner import Runner

    def test_galaxy_no_collection_version() -> None:
        """Test for no collection version in galaxy."""
        collection = RulesCollection()
        collection.register(GalaxyRule())
        failure = "examples/.no_collection_version/galaxy.yml"
        bad_runner = Runner(failure, rules=collection)
        errs = bad_runner.run()
        assert len(errs) == 1

    @pytest.mark.parametrize(
        ("file", "expected"),
        (
            pytest.param(
                "examples/galaxy_tags/galaxy_invalid_format_tags/galaxy.yml",
                ["galaxy[tags-format]"],
                id="tags-format",
            ),
            pytest.param(
                "examples/galaxy_tags/galaxy_invalid_length_tags/galaxy.yml",
                ["galaxy[tags-length]"],
                id="tags-length",
            ),
            pytest.param(
                "examples/galaxy_tags/galaxy_count_tags/galaxy.yml",
                ["galaxy[tags-count]"],
                id="tags-count",
            ),
            pytest.param(
                "examples/galaxy_tags/galaxy_no_required_tags/galaxy.yml",
                ["galaxy[tags]"],
                id="tags",
            ),
            pytest.param(
                "examples/galaxy_tags/pass/galaxy.yml",
                [],
                id="pass",
            ),
            pytest.param(
                "examples/.collection/galaxy.yml",
                ["schema[galaxy]"],
                id="schema",
            ),
            pytest.param(
                "examples/.invalid_dependencies/galaxy.yml",
                [
                    "galaxy[invalid-dependency-version]",
                    "galaxy[invalid-dependency-version]",
                ],
                id="invalid-dependency-version",
            ),
            pytest.param(
                "examples/.no_changelog/galaxy.yml",
                ["galaxy[no-changelog]"],
                id="no-changelog",
            ),
            pytest.param(
                "examples/.no_collection_version/galaxy.yml",
                ["schema[galaxy]", "galaxy[version-missing]"],
                id="no-collection-version",
            ),
            pytest.param(
                "examples/collections/broken_no_runtime/galaxy.yml",
                ["galaxy[no-runtime]"],
                id="broken_no_runtime",
            ),
        ),
    )
    def test_galaxy_rule(
        default_rules_collection: RulesCollection,
        file: str,
        expected: list[str],
    ) -> None:
        """Validate that rule works as intended."""
        results = Runner(file, rules=default_rules_collection).run()

        assert len(results) == len(expected)
        for index, result in enumerate(results):
            assert result.tag == expected[index]
