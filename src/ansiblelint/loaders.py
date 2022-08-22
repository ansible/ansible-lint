"""Utilities for loading various files."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def yaml_from_file(filepath: str | Path) -> Any:
    """Return a loaded YAML file."""
    with open(str(filepath), encoding="utf-8") as content:
        return yaml.load(content, Loader=yaml.FullLoader)
