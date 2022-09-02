"""Implementation of GalaxyCollectionVersionRule."""
from __future__ import annotations

import sys
from functools import total_ordering
from typing import TYPE_CHECKING, Any

from ansiblelint.errors import MatchError
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.utils import LINE_NUMBER_KEY

if TYPE_CHECKING:
    from typing import Optional

    from ansiblelint.constants import odict
    from ansiblelint.file_utils import Lintable


class GalaxyCollectionVersionRule(AnsibleLintRule):
    """Rule for checking collection version is greater than 1.0.0"""

    id = "galaxy-collection-version"
    description = "Confirm via galaxy.yml file if collection version is greater than or equal to 1.0.0"
    severity = "MEDIUM"
    tags = ["metadata"]
    version_added = "v6.5.0 (last update)"

    def matchplay(self, file: Lintable, data: odict[str, Any]) -> list[MatchError]:
        """Return matches found for a specific play (entry in playbook)."""

        if file.kind != "galaxy":
            return []
        if "version" not in data:
            return [
                self.create_matcherror(
                    message="galaxy.yaml should have version tag.",
                    linenumber=data[LINE_NUMBER_KEY],
                    tag="collection-version-missing[galaxy]",
                    filename=file,
                )
            ]
        elif Version(data.get("version")) < Version("1.0.0"):
            return [
                self.create_matcherror(
                    message="collection version should be greater than or equal to 1.0.0",
                    linenumber=data[LINE_NUMBER_KEY],
                    tag="collection-version[galaxy]",
                    filename=file,
                )
            ]


@total_ordering
class Version:
    """Simple class to compare arbitrary versions"""

    def __init__(self, version_string):
        self.components = version_string.split(".")

    def __eq__(self, other):
        other = _coerce(other)
        if not isinstance(other, Version):
            return NotImplemented

        return self.components == other.components

    def __lt__(self, other):
        other = _coerce(other)
        if not isinstance(other, Version):
            return NotImplemented

        return self.components < other.components


def _coerce(other):
    if isinstance(other, str):
        other = Version(other)
    if isinstance(other, (int, float)):
        other = Version(str(other))
    return other


if "pytest" in sys.modules:  # noqa: C901

    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    def test_galaxy_collection_version_positive() -> None:
        """Positive test for collection version in galaxy."""
        collection = RulesCollection()
        collection.register(GalaxyCollectionVersionRule())
        success = "examples/galaxy.yml"
        good_runner = Runner(success, rules=collection)
        assert [] == good_runner.run()

    def test_galaxy_collection_version_negative() -> None:
        """Negative test for collection version in galaxy."""
        collection = RulesCollection()
        collection.register(GalaxyCollectionVersionRule())
        failure = "examples/meta/galaxy.yml"
        bad_runner = Runner(failure, rules=collection)
        errs = bad_runner.run()
        assert len(errs) == 3
