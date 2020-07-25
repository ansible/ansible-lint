"""Console coloring support."""
from enum import Enum


class Color(Enum):
    """Color styles."""

    reset = "0"
    error_code = "1;31"  # bright red
    error_title = "0;31"  # red
    filename = "0;34"  # blue
    linenumber = "0;36"  # cyan
    line = "0;35"  # purple


def colorize(text: str, color: Color) -> str:
    """Return ANSI formated string."""
    return f"\u001b[{color.value}m{text}\u001b[{Color.reset.value}m"
