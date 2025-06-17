"""Utilities for loading various files."""

from __future__ import annotations

import enum
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
except (ImportError, AttributeError):  # pragma: no cover
    from yaml import FullLoader, SafeLoader  # type: ignore[assignment]

if TYPE_CHECKING:
    from pathlib import Path


class IgnoreFile(NamedTuple):
    """IgnoreFile n."""

    default: str
    alternative: str


class IgnoreRuleQualifier(enum.Enum):
    """Extra flags for ignored rules."""

    SKIP = "Force skip, not warning"


class IgnoreRule(NamedTuple):
    """Ignored rule."""

    rule: str
    qualifiers: frozenset[IgnoreRuleQualifier]


IGNORE_FILE = IgnoreFile(".ansible-lint-ignore", ".config/ansible-lint-ignore.txt")

yaml_load = partial(yaml.load, Loader=FullLoader)
yaml_load_safe = partial(yaml.load, Loader=SafeLoader)
_logger = logging.getLogger(__name__)


def yaml_from_file(filepath: str | Path) -> Any:
    """Return a loaded YAML file."""
    with open(str(filepath), encoding="utf-8") as content:
        return yaml_load(content)


def get_ignore_rule(rule: str, qualifiers: str) -> IgnoreRule:
    """Validate qualifiers and return an IgnoreRule."""
    s = set()
    if qualifiers:
        for q in qualifiers.split(","):
            if q == "skip":
                s.add(IgnoreRuleQualifier.SKIP)
            else:
                raise ValueError
    return IgnoreRule(rule, frozenset(s))


def load_ignore_txt(filepath: Path | None = None) -> dict[str, set[IgnoreRule]]:
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
                        fields = entry.split()
                        path = fields[0]
                        rule = fields[1]
                        qualifiers = fields[2] if len(fields) == 3 else ""
                        result[path].add(get_ignore_rule(rule, qualifiers))
                    except ValueError as exc:  # pragma: no cover
                        msg = f"Unable to parse line '{line}' from {ignore_file} file."
                        raise RuntimeError(msg) from exc
    return result


__all__ = [
    "IGNORE_FILE",
    "IgnoreRule",
    "IgnoreRuleQualifier",
    "YAMLError",
    "load_ignore_txt",
    "yaml_from_file",
    "yaml_load",
    "yaml_load_safe",
]
