"""Utilities for loading various files."""

from __future__ import annotations

import logging
import os
from collections import defaultdict
from functools import partial
from typing import TYPE_CHECKING, Any, NamedTuple

import yaml
from yaml import YAMLError

try:
    from yaml import CFullLoader as FullLoader
    from yaml import CSafeLoader as SafeLoader
except (ImportError, AttributeError):
    from yaml import FullLoader, SafeLoader  # type: ignore[assignment]

if TYPE_CHECKING:
    from pathlib import Path


class IgnoreFile(NamedTuple):
    """IgnoreFile n."""

    default: str
    alternative: str


IGNORE_FILE = IgnoreFile(".ansible-lint-ignore", ".config/ansible-lint-ignore.txt")

yaml_load = partial(yaml.load, Loader=FullLoader)
yaml_load_safe = partial(yaml.load, Loader=SafeLoader)
_logger = logging.getLogger(__name__)


def yaml_from_file(filepath: str | Path) -> Any:
    """Return a loaded YAML file."""
    with open(str(filepath), encoding="utf-8") as content:
        return yaml_load(content)


def load_ignore_txt(filepath: Path | None = None) -> dict[str, set[str]]:
    """Return a list of rules to ignore."""
    result = defaultdict(set)

    ignore_file = None

    if filepath:
        if os.path.isfile(filepath):
            ignore_file = str(filepath)
        else:
            _logger.error("Ignore file not found '%s'", ignore_file)
    elif os.path.isfile(IGNORE_FILE.default):
        ignore_file = IGNORE_FILE.default
    elif os.path.isfile(IGNORE_FILE.alternative):
        ignore_file = IGNORE_FILE.alternative

    if ignore_file:
        with open(ignore_file, encoding="utf-8") as _ignore_file:
            _logger.debug("Loading ignores from '%s'", ignore_file)
            for line in _ignore_file:
                entry = line.split("#")[0].rstrip()
                if entry:
                    try:
                        path, rule = entry.split()
                    except ValueError as exc:
                        msg = f"Unable to parse line '{line}' from {ignore_file} file."
                        raise RuntimeError(msg) from exc
                    result[path].add(rule)

    return result


__all__ = [
    "load_ignore_txt",
    "yaml_from_file",
    "yaml_load",
    "yaml_load_safe",
    "YAMLError",
    "IGNORE_FILE",
]
