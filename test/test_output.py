"""Tests for ansiblelint.output BBCode rendering helpers."""

from __future__ import annotations

from ansiblelint.output import Console, console


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
