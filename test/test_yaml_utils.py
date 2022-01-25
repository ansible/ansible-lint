"""Tests for yaml-related utility functions."""
from typing import Any

import pytest

import ansiblelint.yaml_utils
from ansiblelint.file_utils import Lintable


@pytest.fixture
def empty_lintable() -> Lintable:
    """Return a Lintable with no contents."""
    lintable = Lintable("__empty_file__")
    lintable._content = ""
    return lintable


def test_iter_tasks_in_file_with_empty_file(empty_lintable: Lintable) -> None:
    """Make sure that iter_tasks_in_file returns early when files are empty."""
    res = list(
        ansiblelint.yaml_utils.iter_tasks_in_file(empty_lintable, "some-rule-id")
    )
    assert res == []


def test_nested_items_path() -> None:
    """Verify correct function of nested_items_path()."""
    data = {
        "foo": "text",
        "bar": {"some": "text2"},
        "fruits": ["apple", "orange"],
        "answer": [{"forty-two": ["life", "universe", "everything"]}],
    }

    items = [
        ("foo", "text", []),
        ("bar", {"some": "text2"}, []),
        ("some", "text2", ["bar"]),
        ("fruits", ["apple", "orange"], []),
        (0, "apple", ["fruits"]),
        (1, "orange", ["fruits"]),
        ("answer", [{"forty-two": ["life", "universe", "everything"]}], []),
        (0, {"forty-two": ["life", "universe", "everything"]}, ["answer"]),
        ("forty-two", ["life", "universe", "everything"], ["answer", 0]),
        (0, "life", ["answer", 0, "forty-two"]),
        (1, "universe", ["answer", 0, "forty-two"]),
        (2, "everything", ["answer", 0, "forty-two"]),
    ]
    assert list(ansiblelint.yaml_utils.nested_items_path(data)) == items


@pytest.mark.parametrize(
    'invalid_data_input',
    (
        "string",
        42,
        1.234,
        None,
        ("tuple",),
        {"set"},
    ),
)
def test_nested_items_path_raises_typeerror(invalid_data_input: Any) -> None:
    """Verify non-dict/non-list types make nested_items_path() raises TypeError."""
    with pytest.raises(TypeError, match=r"Expected a dict or a list.*"):
        list(ansiblelint.yaml_utils.nested_items_path(invalid_data_input))
