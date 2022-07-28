"""Utilities for loading various files."""
from pathlib import Path
from typing import Any, Union

import yaml


def yaml_from_file(filepath: Union[str, Path]) -> Any:
    """Return a loaded YAML file."""
    with open(str(filepath), encoding="utf-8") as content:
        return yaml.load(content, Loader=yaml.FullLoader)
