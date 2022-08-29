"""Utilities for loading various files."""
from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Any

import yaml
from yaml import YAMLError

try:
    from yaml import CFullLoader as FullLoader
    from yaml import CSafeLoader as SafeLoader
except (ImportError, AttributeError):
    from yaml import FullLoader, SafeLoader  # type: ignore

yaml_load = partial(yaml.load, Loader=FullLoader)
yaml_load_safe = partial(yaml.load, Loader=SafeLoader)


def yaml_from_file(filepath: str | Path) -> Any:
    """Return a loaded YAML file."""
    with open(str(filepath), encoding="utf-8") as content:
        return yaml_load(content)


__all__ = ["yaml_from_file", "yaml_load", "yaml_load_safe", "YAMLError"]
