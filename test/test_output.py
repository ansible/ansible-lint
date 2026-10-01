"""Tests for ansiblelint.output BBCode rendering helpers."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import TYPE_CHECKING

from ansiblelint import output
from ansiblelint.output import (
    Console,
    console,
    console_stderr,
    reconfigure,
    should_do_markup,
)

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_console_render_notset_and_link_nested_with_bold() -> None:
    """[notset] maps correctly and [link] must not corrupt nested [/] closing."""
    rendered = console.render(
        "[bold]see [link=https://example.invalid]docs[/link] now[/]",
    )
    assert "docs" in rendered
    assert "[link=" not in rendered
    assert "[/link]" not in rendered

    notset = console.render("[notset]level[/]")
    assert "level" in notset


def test_console_render_unknown_tag_preserves_raw() -> None:
    """Unknown BBCode tags remain literal and do not break later closes."""
    plain = Console()
    plain.colored = False
    rendered = plain.render("[unknown]x[/] [bold]y[/]")
    assert "[unknown]x" in rendered
    assert "y" in rendered
    # Force PlainStyle mapping paths (uncolored) including notset/failed/success.
    assert "plain" in plain.render("[notset]plain[/] [failed]f[/] [success]s[/]")


def test_bb_helper_edge_cases() -> None:
    """Cover param substitution, empty close, and stack flush branches."""
    mapping = {"bold": ("<b param={param}>", "</b>"), "info": ("<i>", "</i>")}
    stack: list[tuple[str, str | None]] = []
    result: list[str] = []

    output._append_bb_open_tag(  # ruff:ignore[private-member-access]
        "bold",
        "x",
        "[bold=x]",
        stack,
        result,
        mapping,
    )
    assert result == ["<b param=x>"]
    assert stack == [("bold", "x")]

    output._append_bb_close_tag([], result, mapping)  # ruff:ignore[private-member-access]
    assert result[-1] == "[/]"

    output._flush_bb_stack([("info", None), ("unknown", None)], result, mapping)  # ruff:ignore[private-member-access]
    assert "</i>" in result


class _FakeStream:
    """Minimal text stream with a configurable isatty()."""

    def __init__(self, *, tty: bool) -> None:
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


def test_should_do_markup_redirected_stderr_with_xterm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A redirected stream must not be colored just because TERM is xterm."""
    for var in (
        "PY_COLORS",
        "CLICOLOR",
        "FORCE_COLOR",
        "ANSIBLE_FORCE_COLOR",
        "NO_COLOR",
    ):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("TERM", "xterm-256color")

    assert not should_do_markup(_FakeStream(tty=False))  # type: ignore[arg-type]
    assert should_do_markup(_FakeStream(tty=True))  # type: ignore[arg-type]
    # Explicit user request still wins over tty detection.
    monkeypatch.setenv("FORCE_COLOR", "1")
    assert should_do_markup(_FakeStream(tty=False))  # type: ignore[arg-type]


def test_reconfigure_stderr_color_is_independent() -> None:
    """Stderr console can be configured separately from stdout."""
    old = (console.colored, console_stderr.colored)
    try:
        reconfigure(colored=True, stderr_colored=False)
        assert console.colored
        assert not console_stderr.colored
        reconfigure(colored=False)
        assert not console_stderr.colored
    finally:
        console.colored, console_stderr.colored = old


def test_redirected_stderr_has_no_ansi_with_xterm(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Piped stderr must stay free of ANSI codes even when TERM is xterm."""
    playbook = tmp_path / "play.yml"
    playbook.write_text(
        "---\n- hosts: localhost\n  tasks:\n    - ansible.builtin.debug:\n        msg: hi\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    for var in (
        "PY_COLORS",
        "CLICOLOR",
        "FORCE_COLOR",
        "ANSIBLE_FORCE_COLOR",
        "NO_COLOR",
    ):
        env.pop(var, None)
    env["TERM"] = "xterm-256color"
    monkeypatch.chdir(tmp_path)
    proc = subprocess.run(
        [sys.executable, "-m", "ansiblelint", str(playbook)],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    # the failing playbook makes sure the violation summary is printed too
    assert proc.returncode == 2, proc
    assert "Rule Violation Summary" in proc.stderr
    assert "\x1b" not in proc.stderr
