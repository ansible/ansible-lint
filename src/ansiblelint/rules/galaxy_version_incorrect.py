"""Implementation of GalaxyVersionIncorrectRule."""

from __future__ import annotations

import sys
from functools import total_ordering
from typing import TYPE_CHECKING, Any

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable


class GalaxyVersionIncorrectRule(AnsibleLintRule):
    """Rule for checking collection version is greater than 1.0.0."""

    id = "galaxy-version-incorrect"
    description = "Confirm via galaxy.yml file if collection version is greater than or equal to 1.0.0."
    severity = "MEDIUM"
    tags = ["opt-in", "metadata"]
    version_changed = "24.7.0"

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        """Return matches found for a specific play (entry in playbook)."""
        if file.kind != "galaxy":
            return []

        results = []
        version = data.get("version")
        if not version or Version(version) < Version("1.0.0"):
            results.append(
                self.create_matcherror(
                    message="collection version should be greater than or equal to 1.0.0",
                    data=version,
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
        collection.register(GalaxyVersionIncorrectRule())
        success = "examples/.collection/galaxy.yml"
        good_runner = Runner(success, rules=collection)
        assert good_runner.run() == []

    def test_galaxy_collection_version_negative() -> None:
        """Negative test for collection version in galaxy."""
        collection = RulesCollection()
        collection.register(GalaxyVersionIncorrectRule())
        failure = "examples/meta/galaxy.yml"
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
