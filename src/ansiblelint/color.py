"""Console coloring and terminal support."""
from __future__ import annotations

from typing import Any

import rich
import rich.markdown
from rich.console import Console
from rich.default_styles import DEFAULT_STYLES
from rich.style import Style
from rich.syntax import Syntax
from rich.theme import Theme

# WARNING: When making style changes, be sure you test the output of
# `ansible-lint -L` on multiple terminals with dark/light themes, including:
# - iTerm2 (macOS) - bold might not be rendered differently
# - vscode integrated terminal - bold might not be rendered differently, links will not work
#
# When it comes to colors being used, try to match:
# - Ansible official documentation theme, https://docs.ansible.com/ansible/latest/dev_guide/developing_api.html
# - VSCode Ansible extension for syntax highlighting
# - GitHub markdown theme
#
# Current values: (docs)
# codeblock border: #404040
# codeblock background: #edf0f2
# codeblock comment: #6a737d (also italic)
# teletype-text: #e74c3c (red)
# teletype-text-border: 1px solid #e1e4e5 (background white)
# text: #404040
# codeblock other-text: #555555 (black-ish)
# codeblock property: #22863a (green)
# codeblock integer: 032f62 (blue)
# codeblock command: #0086b3 (blue) - [shell]
# == python ==
# class: #445588 (dark blue and bold)
# docstring: #dd1144 (red)
# self: #999999 (light-gray)
# method/function: #990000 (dark-red)
# number: #009999 cyan
# keywords (def,None,False,len,from,import): #007020 (green) bold
# super|dict|print: #0086b3 light-blue
# __name__: #bb60d5 (magenta)
# string: #dd1144 (light-red)
DEFAULT_STYLES.update(
    {
        # "code": Style(color="bright_black", bgcolor="red"),
        "markdown.code": Style(color="bright_black"),
        "markdown.code_block": Style(dim=True, color="cyan"),
    }
)


_theme = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "danger": "bold red",
        "title": "yellow",
        "error": "bright_red",
        "filename": "blue",
    }
)
console_options: dict[str, Any] = {"emoji": False, "theme": _theme, "soft_wrap": True}
console_options_stderr = console_options.copy()
console_options_stderr["stderr"] = True

console = rich.get_console()
console_stderr = Console(**console_options_stderr)


def reconfigure(new_options: dict[str, Any]) -> None:
    """Reconfigure console options."""
    global console_options  # pylint: disable=global-statement,invalid-name
    global console_stderr  # pylint: disable=global-statement,invalid-name,global-variable-not-assigned

    console_options = new_options
    rich.reconfigure(**new_options)
    # see https://github.com/willmcgugan/rich/discussions/484#discussioncomment-200182
    new_console_options_stderr = console_options.copy()
    new_console_options_stderr["stderr"] = True
    tmp_console = Console(**new_console_options_stderr)
    console_stderr.__dict__ = tmp_console.__dict__


def render_yaml(text: str) -> Syntax:
    """Colorize YAMl for nice display."""
    return Syntax(text, "yaml", theme="ansi_dark")


# pylint: disable=redefined-outer-name,unused-argument
def _rich_heading_custom_rich_console(
    self: rich.markdown.Heading,
    console: rich.console.Console,
    options: rich.console.ConsoleOptions,
) -> rich.console.RenderResult:
    """Override for rich console heading."""
    yield f"[bold]{self.level * '#'} {self.text}[/]"


# pylint: disable=redefined-outer-name,unused-argument
def _rich_codeblock_custom_rich_console(
    self: rich.markdown.CodeBlock,
    console: Console,
    options: rich.console.ConsoleOptions,
) -> rich.console.RenderResult:
    code = str(self.text).rstrip()
    syntax = Syntax(
        code,
        self.lexer_name,
        theme=self.theme,
        word_wrap=True,
        background_color="default",
    )
    yield syntax


# Monkey-patch rich to alter its rendering of headings
# https://github.com/python/mypy/issues/2427
rich.markdown.Heading.__rich_console__ = _rich_heading_custom_rich_console  # type: ignore
rich.markdown.CodeBlock.__rich_console__ = _rich_codeblock_custom_rich_console  # type: ignore
