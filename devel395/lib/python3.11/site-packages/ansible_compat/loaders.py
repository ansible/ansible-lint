"""Utilities for loading various files."""
from __future__ import annotations

import os
from typing import Any

import yaml

from ansible_compat.errors import InvalidPrerequisiteError


def yaml_from_file(filepath: str) -> Any:
    """Return a loaded YAML file."""
    with open(filepath, encoding="utf-8") as content:
        return yaml.load(content, Loader=yaml.FullLoader)


def colpath_from_path(filepath: str) -> str | None:
    """Return a FQCN from a path."""
    galaxy_file = f"{filepath}/galaxy.yml"
    if os.path.exists(galaxy_file):
        galaxy = yaml_from_file(galaxy_file)
        for k in ("namespace", "name"):
            if k not in galaxy:
                raise InvalidPrerequisiteError(
                    f"{galaxy_file} is missing the following mandatory field {k}"
                )
        return f"{galaxy['namespace']}/{galaxy['name']}"
    return None
