"""Implementation of GalaxyRule."""
from __future__ import annotations

import os
import sys
from functools import total_ordering
from typing import TYPE_CHECKING, Any

import pytest

from ansiblelint.constants import LINE_NUMBER_KEY
from ansiblelint.errors import MatchError
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable


class GalaxyRule(AnsibleLintRule):
    """Rule for checking collection version is greater than 1.0.0 and checking for changelog."""

    id = "galaxy"
    description = "Confirm via galaxy.yml file if collection version is greater than or equal to 1.0.0 and check for changelog."
    severity = "MEDIUM"
    tags = ["metadata"]
    version_added = "v6.11.0 (last update)"

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        """Return matches found for a specific play (entry in playbook)."""
        if file.kind != "galaxy":  # type: ignore
            return []

        results = []

        if "version" not in data:
            results.append(
                self.create_matcherror(
                    message="galaxy.yaml should have version tag.",
                    linenumber=data[LINE_NUMBER_KEY],
                    tag="galaxy[version-missing]",
                    filename=file,
                )
            )
            # returning here as it does not make sense
            # to continue for version check below
            return results

        version = data.get("version")
        if Version(version) < Version("1.0.0"):
            results.append(
                self.create_matcherror(
                    message="collection version should be greater than or equal to 1.0.0",
                    # pylint: disable=protected-access
                    linenumber=version._line_number,
                    tag="galaxy[version-incorrect]",
                    filename=file,
                )
            )

        # Changelog Check - building off Galaxy rule as there is no current way to check
        # for a nonexistent file

        base_path = os.path.split(str(file.abspath))[0]
        changelog_found = 0
        changelog_paths = [
            os.path.join(base_path, "changelogs", "changelog.yaml"),
            os.path.join(base_path, "CHANGELOG.rst"),
            os.path.join(base_path, "CHANGELOG.md"),
        ]

        for path in changelog_paths:
            if os.path.isfile(path):
                changelog_found = 1

        if not changelog_found:
            results.append(
                self.create_matcherror(
                    message="No changelog found. Please add a changelog file. Refer to the galaxy.md file for more info.",
                    tag="galaxy[no-changelog]",
                    filename=file,
                )
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
        try:
            other = _coerce(other)
        except NotImplementedError:
            return NotImplemented

        return self.components < other.components


def _coerce(other: object) -> Version:
    if isinstance(other, str):
        other = Version(other)
    if isinstance(other, (int, float)):
        other = Version(str(other))
    if isinstance(other, Version):
        return other
    raise NotImplementedError(f"Unable to coerce object type {type(other)} to Version")


if "pytest" in sys.modules:  # noqa: C901

    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    def test_galaxy_collection_version_positive() -> None:
        """Positive test for collection version in galaxy."""
        collection = RulesCollection()
        collection.register(GalaxyRule())
        success = "examples/collection/galaxy.yml"
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
        failure = "examples/no_collection_version/galaxy.yml"
        bad_runner = Runner(failure, rules=collection)
        errs = bad_runner.run()
        assert len(errs) == 1

    def test_changelog_present() -> None:
        """Positive test for finding a changelog."""
        collection = RulesCollection()
        collection.register(GalaxyRule())
        good_runner = Runner("examples/collection/galaxy.yml", rules=collection)
        assert [] == good_runner.run()

    def test_changelog_missing() -> None:
        """Negative test for finding a changelog."""
        collection = RulesCollection()
        collection.register(GalaxyRule())
        bad_runner = Runner("examples/no_changelog/galaxy.yml", rules=collection)
        result = bad_runner.run()
        assert len(result) == 1
        for item in result:
            assert item.tag == "galaxy[no-changelog]"

    def test_version_class() -> None:
        """Test for version class."""
        v = Version("1.0.0")
        assert v == Version("1.0.0")

    def test_coerce() -> None:
        """Test for _coerce function."""
        assert _coerce("1.0") == Version("1.0")
        assert _coerce(1.0) == Version("1.0")
        expected = "Unable to coerce object type"
        with pytest.raises(NotImplementedError, match=expected):
            _coerce(type(Version))
