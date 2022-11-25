"""Text utils."""
from __future__ import annotations

import re


def strip_ansi_escape(data: str | bytes) -> str:
    """Remove all ANSI escapes from string or bytes.

    If bytes is passed instead of string, it will be converted to string
    using UTF-8.
    """
    if isinstance(data, bytes):  # pragma: no branch
        data = data.decode("utf-8")

    return re.sub(r"\x1b[^m]*m", "", data)


def toidentifier(text: str) -> str:
    """Convert unsafe chars to ones allowed in variables."""
    result = re.sub(r"[\s-]+", "_", text)
    if not result.isidentifier():
        raise RuntimeError(
            f"Unable to convert role name '{text}' to valid variable name."
        )
    return result


# https://www.python.org/dev/peps/pep-0616/
def removeprefix(self: str, prefix: str) -> str:
    """Remove prefix from string."""
    if self.startswith(prefix):
        return self[len(prefix) :]
    return self[:]
