"""Console support: coloring and terminal code."""

# cspell: ignore mdcat, mdless, bbcode

from __future__ import annotations

import dataclasses
import os
import re
import shutil
import subprocess
import sys

# WARNING: When making style changes, be sure you test the output of
# `ansible-lint -L` on multiple terminals with dark/light themes, including:
# - iTerm2 (macOS) - bold might not be rendered differently
# - vscode integrated terminal - bold might not be rendered differently, links will not work
#
# When it comes to colors being used, try to match:
# - Ansible official documentation theme, https://docs.ansible.com/projects/ansible/latest/dev_guide/developing_api.html
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
# See: https://github.com/ansible/ansible-dev-environment/blob/main/src/ansible_dev_environment/output.py
from collections import UserString
from collections.abc import Callable
from dataclasses import dataclass
from io import StringIO
from typing import Any, TextIO

from ansiblelint.logger import _logger

md_cmd: str | None = None

md_renderers = {
    "mdcat": ["mdcat"],  # (rust)
    "rich-cli": ["rich-cli", "--markdown"],  # (python)
    "glow": ["glow"],  # nice output but hyperlinks are exploded (go)
    "mdless": [
        "mdless",
        "--autolink",
        "--no-pager",
    ],  # ugly heading, no hyperlinks (ruby)
}

_styles = (
    "dim",
    "b",
    # logging
    "notset",
    "debug",
    "info",
    "warning",
    "error",
    "critical",
    # results
    "failed",
    "success",
    # reset
    "normal",
    # data types
    "number",
    "path",
)
RE_BB_LINK_PATTERN = re.compile(
    r"\[link=([^\]]+)\]((?:[^\[]|\[(?!\/link\]))+)\[/link\]"
)


# Based on Ansible implementation
def to_bool(value: Any) -> bool:  # pragma: no cover
    """Return a bool for the arg."""
    if value is None or isinstance(value, bool):
        return bool(value)
    if isinstance(value, str):
        value = value.lower()
    return value in ("yes", "on", "1", "true", 1)


def should_do_markup(stream: TextIO = sys.stdout) -> bool:  # pragma: no cover
    """Decide about use of ANSI colors."""
    py_colors = None

    # https://xkcd.com/927/
    for env_var in ["PY_COLORS", "CLICOLOR", "FORCE_COLOR", "ANSIBLE_FORCE_COLOR"]:
        value = os.environ.get(env_var, None)
        if value is not None:
            py_colors = to_bool(value)
            break

    # If deliberately disabled colors
    if os.environ.get("NO_COLOR", None):
        return False

    # User configuration requested colors
    if py_colors is not None:
        return to_bool(py_colors)

    term = os.environ.get("TERM", "")
    if "xterm" in term:
        return True

    if term == "dumb":
        return False

    # Use tty detection logic as last resort because there are numerous
    # factors that can make isatty return a misleading value, including:
    # - stdin.isatty() is the only one returning true, even on a real terminal
    # - stderr returning false if user user uses a error stream coloring solution
    return stream.isatty()


@dataclasses.dataclass
class PlainStyle:
    """Theme."""

    failed: str = ""
    success: str = ""
    normal: str = ""
    dim: str = ""
    bold: str = ""
    # logging
    notset: str = ""
    debug: str = ""
    info: str = ""
    warning: str = ""
    error: str = ""
    critical: str = ""

    # data types
    number: str = ""
    path: str = ""
    link: str = ""

    @classmethod
    def render_link(cls, uri: str, label: str | None = None) -> str:
        """Return a link."""
        return label or uri


@dataclasses.dataclass
class AnsiStyle(PlainStyle):
    """Theme."""

    @dataclass
    class ANSI:
        """Color constants."""

        BLACK = "\033[30m"
        RED = "\033[31m"
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        BLUE = "\033[34m"
        MAGENTA = "\033[35m"
        CYAN = "\033[36m"
        WHITE = "\033[37m"
        GREY = "\033[90m"  # Bright black?
        BRIGHT_RED = "\033[91m"
        BRIGHT_GREEN = "\033[92m"
        BRIGHT_YELLOW = "\033[93m"
        BRIGHT_BLUE = "\033[94m"
        BRIGHT_MAGENTA = "\033[95m"
        BRIGHT_CYAN = "\033[96m"
        BRIGHT_WHITE = "\033[97m"
        END = "\033[0m"
        # more complex
        BOLD = "\033[1m"
        DIM = "\033[2m"
        BOLD_CYAN = "\033[1;36m"

    warning: str = "\033[33m"  # yellow
    error: str = ANSI.RED  # "\033[31m"  # red
    info: str = ANSI.BLUE
    debug: str = ANSI.BLUE
    notset: str = ANSI.BLUE

    failed: str = ANSI.RED
    success: str = ANSI.GREEN

    normal: str = ANSI.END
    dim: str = ANSI.DIM
    bold: str = ANSI.BOLD
    # data types
    number: str = ANSI.BOLD_CYAN
    path: str = ANSI.MAGENTA  # do not use same color as link
    link: str = ANSI.BLUE

    @classmethod
    def render_link(cls, uri: str, label: str | None = None) -> str:
        """Return a link."""
        if label is None:
            label = uri
        parameters = ""

        # OSC 8 ; params ; URI ST <name> OSC 8 ;; ST
        escape_mask = "\033]8;{};{}\033\\{}\033]8;;\033\\"

        return cls.link + escape_mask.format(parameters, uri, label) + cls.normal


def _bbcode_to_ansi_mappings(style: type[PlainStyle]) -> dict[str, tuple[str, str]]:
    return {
        "bold": (style.bold, style.normal),
        "dim": (style.dim, style.normal),
        "warning": (style.warning, style.normal),
        "error": (style.error, style.normal),
        "info": (style.info, style.normal),
        "debug": (style.debug, style.normal),
        "notset": (style.notset, style.normal),
        "repr.path": (style.path, style.normal),
        "repr.number": (style.number, style.normal),
        "repr.link": (style.link, style.normal),
        "failed": (style.failed, style.normal),
        "success": (style.success, style.normal),
    }


def _replace_bb_links(text: str, style: type[PlainStyle]) -> str:
    def replacement(match: re.Match[str]) -> str:
        url = match.group(1)
        title = match.group(2)
        return style.render_link(url, title)

    return RE_BB_LINK_PATTERN.sub(replacement, text)


def _append_bb_open_tag(
    tag: str,
    param: str | None,
    raw: str,
    stack: list[tuple[str, str | None]],
    result: list[str],
    bbcode_to_ansi: dict[str, tuple[str, str]],
) -> None:
    if tag not in bbcode_to_ansi:
        result.append(raw)
        # Link tags are closed by [/link] (handled later); do not push onto the
        # generic [/] stack or nested tag closing will become misaligned.
        if tag != "link":
            stack.append(("unknown", None))
        return
    stack.append((tag, param))
    opening, _ = bbcode_to_ansi[tag]
    if param:
        opening = opening.replace("{param}", param)
    result.append(opening)


def _append_bb_close_tag(
    stack: list[tuple[str, str | None]],
    result: list[str],
    bbcode_to_ansi: dict[str, tuple[str, str]],
) -> None:
    if not stack:
        result.append("[/]")
        return
    open_tag, _ = stack.pop()
    if open_tag in bbcode_to_ansi:
        _, closing = bbcode_to_ansi[open_tag]
        result.append(closing)
    else:
        result.append("[/]")


def _flush_bb_stack(
    stack: list[tuple[str, str | None]],
    result: list[str],
    bbcode_to_ansi: dict[str, tuple[str, str]],
) -> None:
    while stack:
        open_tag, _ = stack.pop()
        if open_tag != "unknown":
            _, closing = bbcode_to_ansi[open_tag]
            result.append(closing)


def _replace_bb_tags(
    text: str,
    tag_pattern: re.Pattern[str],
    bbcode_to_ansi: dict[str, tuple[str, str]],
) -> str:
    stack: list[tuple[str, str | None]] = []
    result: list[str] = []
    pos = 0

    for match in tag_pattern.finditer(text):
        start, end = match.span()
        tag = match.group(1)
        param = match.group(2)

        result.append(text[pos:start])
        pos = end

        if tag:
            _append_bb_open_tag(
                tag, param, match.group(0), stack, result, bbcode_to_ansi
            )
        else:
            _append_bb_close_tag(stack, result, bbcode_to_ansi)

    result.append(text[pos:])
    _flush_bb_stack(stack, result, bbcode_to_ansi)
    return "".join(result)


class Markdown(UserString):
    """Markdown string."""

    def display(self) -> None:
        """Display markdown text in the terminal using an external renderer if available."""
        global md_cmd  # pylint: disable=global-statement
        if md_cmd is None:
            for v in md_renderers:
                if shutil.which(v):
                    md_cmd = v
                    break
            if not md_cmd:
                msg = f"No know markdown renderer found ({', '.join(md_renderers)}), output as plain text."
                _logger.warning(msg)
                md_cmd = ""
            else:
                msg = f"Using markdown renderer: {md_cmd}"
                _logger.info(msg)

        if md_cmd:
            subprocess.run(  # noqa: S603
                md_renderers[md_cmd],
                input=self.data,
                text=True,
                check=False,
            )
        else:
            console.print(self.data)


color: bool = True


# https://peps.python.org/pep-3101/
__all__ = ("Console", "color")


class Console:
    """Console."""

    colored: bool = True
    style: type[PlainStyle] = AnsiStyle
    # Regex to find opening tags and their content
    tag_pattern = re.compile(r"\[([\w\.]+)(?:=(.*?))?\]|\[/\]")

    def __init__(self, file: TextIO | None = sys.stdout):
        """Console constructor."""
        self._file = file

    def print(
        self,
        *values: Any,
        sep: str | None = " ",
        end: str | None = "\n",
        file: TextIO | None = None,
        flush: bool = False,
    ) -> None:
        """Internal print implementation."""
        buffer = StringIO()
        print(*values, sep=sep, end="", file=buffer, flush=True)
        buffer.seek(0)
        data = buffer.read()
        print(self.render(data), end=end, file=file or self._file, flush=flush)

    def render(self, text: str) -> str:
        """Parses a string containing nested BBCode with a generic block terminator ([/])."""
        style: type[PlainStyle] = AnsiStyle if self.colored else PlainStyle
        bbcode_to_ansi = _bbcode_to_ansi_mappings(style)
        return _replace_bb_links(
            _replace_bb_tags(text, self.tag_pattern, bbcode_to_ansi),
            style,
        )


console = Console()
console_stderr = Console(file=sys.stderr)


def reconfigure(colored: bool | None = None) -> None:
    """Reconfigure console options."""
    if colored is not None:
        console.colored = colored
        console_stderr.colored = colored


def render_yaml(text: str) -> str:
    """Colorize YAMl for nice display."""
    return text


_ReStringMatch = re.Match[str]  # regex match object
_ReSubCallable = Callable[[_ReStringMatch], str]  # Callable invoked by re.sub
_EscapeSubMethod = Callable[[_ReSubCallable, str, int], str]


if __name__ == "__main__":
    console.print("foo [bold]bold[/] [repr.number]123[/] [repr.path]/dev/null[/]")
    console.print("foo [dim]dimmed[/]")
    console.print("foo [error]dimmed[/] [link=https://google.com]google.com[/link]")
    console.print("foo [error]dimmed[/] [link=https://google.com]name[casing][/link]")
