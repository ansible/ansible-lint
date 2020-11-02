"""Console coloring and terminal support."""
from typing import Any, Dict

import rich
from rich.console import Console
from rich.theme import Theme

_theme = Theme({
    "info": "cyan",
    "warning": "dim yellow",
    "danger": "bold red",
    "title": "yellow",
    "error_code": "bright_red",
    "error_title": "red",
    "filename": "blue"
})
console_options: Dict[str, Any] = {
    "emoji": False,
    "theme": _theme,
    "soft_wrap": True
}

console = rich.get_console()
console_stderr = Console(**console_options, stderr=True)


def reconfigure(new_options: Dict[str, Any]):
    """Reconfigure console options."""
    global console_options  # pylint: disable=global-statement
    global console_stderr  # pylint: disable=global-statement

    console_options = new_options
    rich.reconfigure(**new_options)
    # see https://github.com/willmcgugan/rich/discussions/484#discussioncomment-200182
    tmp_console = Console(**console_options, stderr=True)
    console_stderr.__dict__ = tmp_console.__dict__


def render_yaml(text: str):
    """Colorize YAMl for nice display."""
    return rich.syntax.Syntax(text, 'yaml', theme="ansi_dark")
