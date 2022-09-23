"""Implementation of GalaxyRule."""
from __future__ import annotations

import sys
from functools import total_ordering
from typing import TYPE_CHECKING, Any

from ansiblelint.constants import LINE_NUMBER_KEY
from ansiblelint.errors import MatchError
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable


class GalaxyRule(AnsibleLintRule):
    """Rule for checking collection version is greater than 1.0.0."""

    id = "galaxy"
    description = "Confirm via galaxy.yml file if collection version is greater than or equal to 1.0.0"
    severity = "MEDIUM"
    tags = ["metadata", "opt-in", "experimental"]
    version_added = "v6.6.0 (last update)"

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        """Return matches found for a specific play (entry in playbook)."""
        if file.kind != "galaxy":  # type: ignore
            return []
        if "version" not in data:
            return [
                self.create_matcherror(
                    message="galaxy.yaml should have version tag.",
                    linenumber=data[LINE_NUMBER_KEY],
                    tag="galaxy[version-missing]",
                    filename=file,
                )
            ]
        version = data.get("version")
        if Version(version) < Version("1.0.0"):
            return [
                self.create_matcherror(
                    message="collection version should be greater than or equal to 1.0.0",
                    # pylint: disable=protected-access
                    linenumber=version._line_number,
                    tag="galaxy[version-incorrect]",
                    filename=file,
                )
            ]
        return []


@total_ordering
class Version:
    """Simple class to compare arbitrary versions."""

    def __init__(self, version_string: str):
        """Construct a Version object."""
        self.components = version_string.split(".")

    def __eq__(self, other: object) -> bool:
        """Implement equality comparison."""
        other = _coerce(other)
        if not isinstance(other, Version):
            return NotImplemented

        return self.components == other.components

    def __lt__(self, other: Version) -> bool:
        """Implement lower-than operation."""
        other = _coerce(other)
        if not isinstance(other, Version):
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
