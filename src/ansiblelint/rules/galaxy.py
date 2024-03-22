"""Implementation of GalaxyRule."""

from __future__ import annotations

import sys
from functools import total_ordering
from typing import TYPE_CHECKING, Any

from ansiblelint.constants import FILENAME_KEY, LINE_NUMBER_KEY
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable


class GalaxyRule(AnsibleLintRule):
    """Rule for checking collection version is greater than 1.0.0 and checking for changelog."""

    id = "galaxy"
    description = "Confirm via galaxy.yml file if collection version is greater than or equal to 1.0.0 and check for changelog."
    severity = "MEDIUM"
    tags = ["metadata"]
    version_added = "v6.11.0 (last update)"
    _ids = {
        "galaxy[tags]": "galaxy.yaml must have one of the required tags",
        "galaxy[no-changelog]": "No changelog found. Please add a changelog file. Refer to the galaxy.md file for more info.",
        "galaxy[version-missing]": "galaxy.yaml should have version tag.",
        "galaxy[version-incorrect]": "collection version should be greater than or equal to 1.0.0",
        "galaxy[no-runtime]": "meta/runtime.yml file not found.",
        "galaxy[invalid-dependency-version]": "Invalid collection metadata. Dependency version spec range is invalid",
    }

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        """Return matches found for a specific play (entry in playbook)."""
        if file.kind != "galaxy":  # type: ignore[comparison-overlap]
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
            base_path / "CHANGELOG.rst",
            base_path / "CHANGELOG.md",
        ]

        for path in changelog_paths:
            if path.is_file():
                changelog_found = 1
        galaxy_tag_list = data.get("tags")
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

        if "version" not in data:
            results.append(
                self.create_matcherror(
                    message="galaxy.yaml should have version tag.",
                    lineno=data[LINE_NUMBER_KEY],
                    tag="galaxy[version-missing]",
                    filename=file,
                ),
            )
            return results
            # returning here as it does not make sense
            # to continue for version check below

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

        if not (base_path / "meta" / "runtime.yml").is_file():
            results.append(
                self.create_matcherror(
                    message="meta/runtime.yml file not found.",
                    tag="galaxy[no-runtime]",
                    filename=file,
                ),
            )

        return results


@total_ordering
class Version:
    """Simple class to compare arbitrary versions."""

    def __init__(self, version_string: str):
        """Construct a Version object."""
        self.components = version_string.split(".")

    def __eq__(self, other: object) -> bool:
        """Implement equality comparison."""
        try:
            other = _coerce(other)
        except NotImplementedError:
            return NotImplemented

        return self.components == other.components

    def __lt__(self, other: Version) -> bool:
        """Implement lower-than operation."""
        other = _coerce(other)

        return self.components < other.components


def _coerce(other: object) -> Version:
    if isinstance(other, str):
        other = Version(other)
    if isinstance(other, int | float):
        other = Version(str(other))
    if isinstance(other, Version):
        return other
    msg = f"Unable to coerce object type {type(other)} to Version"
    raise NotImplementedError(msg)


if "pytest" in sys.modules:
    import pytest

    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.runner import Runner

    def test_galaxy_collection_version_positive() -> None:
        """Positive test for collection version in galaxy."""
        collection = RulesCollection()
        collection.register(GalaxyRule())
        success = "examples/.collection/galaxy.yml"
        good_runner = Runner(success, rules=collection)
        assert [] == good_runner.run()

    def test_galaxy_collection_version_negative() -> None:
        """Negative test for collection version in galaxy."""
        collection = RulesCollection()
        collection.register(GalaxyRule())
        failure = "examples/meta/galaxy.yml"
        bad_runner = Runner(failure, rules=collection)
        errs = bad_runner.run()
        assert len(errs) == 1

    def test_galaxy_no_collection_version() -> None:
        """Test for no collection version in galaxy."""
        collection = RulesCollection()
        collection.register(GalaxyRule())
        failure = "examples/.no_collection_version/galaxy.yml"
        bad_runner = Runner(failure, rules=collection)
        errs = bad_runner.run()
        assert len(errs) == 1

    def test_version_class() -> None:
        """Test for version class."""
        v = Version("1.0.0")
        assert v == Version("1.0.0")
        assert v != NotImplemented

    def test_coerce() -> None:
        """Test for _coerce function."""
        assert _coerce("1.0") == Version("1.0")
        assert _coerce(1.0) == Version("1.0")
        expected = "Unable to coerce object type"
        with pytest.raises(NotImplementedError, match=expected):
            _coerce(type(Version))

    @pytest.mark.parametrize(
        ("file", "expected"),
        (
            pytest.param(
                "examples/galaxy_no_required_tags/fail/galaxy.yml",
                ["galaxy[tags]"],
                id="tags",
            ),
            pytest.param(
                "examples/galaxy_no_required_tags/pass/galaxy.yml",
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
