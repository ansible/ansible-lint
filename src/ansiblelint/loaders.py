"""Utilities for loading various files."""
from __future__ import annotations

import logging
import os
from collections import defaultdict
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

IGNORE_TXT = ".ansible-lint-ignore"
yaml_load = partial(yaml.load, Loader=FullLoader)
yaml_load_safe = partial(yaml.load, Loader=SafeLoader)
_logger = logging.getLogger(__name__)


def yaml_from_file(filepath: str | Path) -> Any:
    """Return a loaded YAML file."""
    with open(str(filepath), encoding="utf-8") as content:
        return yaml_load(content)


def load_ignore_txt(filepath: str | Path = IGNORE_TXT) -> dict[str, set[str]]:
    """Return a list of rules to ignore."""
    result = defaultdict(set)
    if os.path.isfile(filepath):
        with open(str(filepath), encoding="utf-8") as content:
            _logger.debug("Loading ignores from %s", filepath)
            for line in content:
                entry = line.split("#")[0].rstrip()
                if entry:
                    try:
                        path, rule = entry.split()
                    except ValueError as exc:
                        raise RuntimeError(
                            f"Unable to parse line '{line}' from {filepath} file."
                        ) from exc
                    result[path].add(rule)
    return result


__all__ = [
    "load_ignore_txt",
    "yaml_from_file",
    "yaml_load",
    "yaml_load_safe",
    "YAMLError",
]
