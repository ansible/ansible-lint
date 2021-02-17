"""Utilities for loading various files."""
from typing import Any

import yaml


def yaml_from_file(filepath: str) -> Any:
    """Return a loaded YAML file."""
    with open(filepath) as content:
        return yaml.load(content, Loader=yaml.FullLoader)
