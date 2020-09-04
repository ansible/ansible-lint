"""Console coloring and terminal support."""
import sys
from enum import Enum

from rich.console import Console
from rich.theme import Theme

_theme = Theme({
    "info": "cyan",
    "warning": "dim yellow",
    "danger": "bold red",
    "title": "yellow"
})
console = Console(theme=_theme)
console_stderr = Console(file=sys.stderr, theme=_theme)


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
