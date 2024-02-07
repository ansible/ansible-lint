"""Tests for text module."""

from typing import Any

import pytest

from ansiblelint.text import has_glob, has_jinja, strip_ansi_escape, toidentifier


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        pytest.param("\x1b[1;31mHello", "Hello", id="0"),
        pytest.param("\x1b[2;37;41mExample_file.zip", "Example_file.zip", id="1"),
        pytest.param(b"ansible-lint", "ansible-lint", id="2"),
    ),
)
def test_strip_ansi_escape(value: Any, expected: str) -> None:
    """Tests for strip_ansi_escape()."""
    assert strip_ansi_escape(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        pytest.param("foo-bar", "foo_bar", id="0"),
        pytest.param("foo--bar", "foo_bar", id="1"),
    ),
)
def test_toidentifier(value: Any, expected: str) -> None:
    """Tests for toidentifier()."""
    assert toidentifier(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    (pytest.param("example_test.zip", "Unable to convert role name", id="0"),),
)
def test_toidentifier_fail(value: Any, expected: str) -> None:
    """Tests for toidentifier()."""
    with pytest.raises(RuntimeError) as err:
        toidentifier(value)
    assert str(err.value).find(expected) > -1


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        pytest.param("", False, id="0"),
        pytest.param("{{ }}", True, id="1"),
        pytest.param("foo {# #} bar", True, id="2"),
        pytest.param("foo \n{% %} bar", True, id="3"),
        pytest.param(None, False, id="4"),
        pytest.param(42, False, id="5"),
        pytest.param(True, False, id="6"),
    ),
)
def test_has_jinja(value: Any, expected: bool) -> None:
    """Tests for has_jinja()."""
    assert has_jinja(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        pytest.param("", False, id="0"),
        pytest.param("*", True, id="1"),
        pytest.param("foo.*", True, id="2"),
        pytest.param(None, False, id="4"),
        pytest.param(42, False, id="5"),
        pytest.param(True, False, id="6"),
    ),
)
def test_has_glob(value: Any, expected: bool) -> None:
    """Tests for has_jinja()."""
    assert has_glob(value) == expected
