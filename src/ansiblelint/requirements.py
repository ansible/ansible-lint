"""Utilities for checking python packages requirements."""

import importlib_metadata
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version


class Reqs(dict[str, SpecifierSet]):
    """Utility class for working with package dependencies."""

    reqs: dict[str, SpecifierSet]

    def __init__(self, name: str = "ansible-lint") -> None:
        """Load linter metadata requirements."""
        for req_str in importlib_metadata.metadata(name).json["requires_dist"]:
            req = Requirement(req_str)
            if req.name:
                self[req.name] = req.specifier

    def matches(self, req_name: str, req_version: str | Version) -> bool:
        """Verify if given version is matching current metadata dependencies."""
        if req_name not in self:
            return False
        return all(
            specifier.contains(str(req_version), prereleases=True)
            for specifier in self[req_name]
        )
