"""Tests for text module."""
from typing import Any

import pytest

from ansiblelint.text import has_glob, has_jinja


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
