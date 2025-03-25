"""Text utils."""

from __future__ import annotations

import re
from functools import cache

RE_HAS_JINJA = re.compile(r"{[{%#].*[%#}]}", re.DOTALL)
RE_HAS_GLOB = re.compile(r"[][*?]")
RE_IS_FQCN_OR_NAME = re.compile(r"^\w+(\.\w+){2,100}$|^\w+$")
RE_STRIP_ANSI_ESCAPE = re.compile(r"\x1b[^m]*m")
RE_TO_IDENTIFIER = re.compile(r"[\s-]+")


def strip_ansi_escape(data: str | bytes) -> str:
    """Remove all ANSI escapes from string or bytes.

    If bytes is passed instead of string, it will be converted to string
    using UTF-8.
    """
    if isinstance(data, bytes):  # pragma: no branch
        data = data.decode("utf-8")

    return RE_STRIP_ANSI_ESCAPE.sub("", data)


def toidentifier(text: str) -> str:
    """Convert unsafe chars to ones allowed in variables."""
    result = RE_TO_IDENTIFIER.sub("_", text)
    if not result.isidentifier():
        msg = f"Unable to convert role name '{text}' to valid variable name."
        raise RuntimeError(msg)
    return result


# https://www.python.org/dev/peps/pep-0616/
def removeprefix(text: str, prefix: str) -> str:
    """Remove prefix from string."""
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text[:]


@cache
def has_jinja(value: str) -> bool:
    """Return true if a string seems to contain jinja templating."""
    return bool(isinstance(value, str) and RE_HAS_JINJA.search(value))


@cache
def has_glob(value: str) -> bool:
    """Return true if a string looks like having a glob pattern."""
    return bool(isinstance(value, str) and RE_HAS_GLOB.search(value))


@cache
def is_fqcn_or_name(value: str) -> bool:
    """Return true if a string seems to be a module/filter old name or a fully qualified one."""
    return bool(isinstance(value, str) and RE_IS_FQCN_OR_NAME.search(value))


@cache
def is_fqcn(value: str) -> bool:
    """Return true if a string seems to be a fully qualified collection name."""
    match = RE_IS_FQCN_OR_NAME.search(value)
    return bool(isinstance(value, str) and match and match.group(1))
