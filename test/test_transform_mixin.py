"""Tests for TransformMixin."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ansiblelint.rules import TransformMixin

if TYPE_CHECKING:
    from typing import Any, Dict, List, MutableMapping, MutableSequence, Type, Union


DUMMY_MAP: dict[str, Any] = {
    "foo": "text",
    "bar": {"some": "text2"},
    "fruits": ["apple", "orange"],
    "answer": [{"forty-two": ["life", "universe", "everything"]}],
}
DUMMY_LIST: list[dict[str, Any]] = [
    {"foo": "text"},
    {"bar": {"some": "text2"}, "fruits": ["apple", "orange"]},
    {"answer": [{"forty-two": ["life", "universe", "everything"]}]},
]


@pytest.mark.parametrize(
    ("yaml_path", "data", "expected_error"),
    (
        ([0], DUMMY_MAP, KeyError),
        (["bar", 0], DUMMY_MAP, KeyError),
        (["fruits", 100], DUMMY_MAP, IndexError),
        (["answer", 1], DUMMY_MAP, IndexError),
        (["answer", 0, 42], DUMMY_MAP, KeyError),
        (["answer", 0, "42"], DUMMY_MAP, KeyError),
        ([100], DUMMY_LIST, IndexError),
        ([0, 0], DUMMY_LIST, KeyError),
        ([0, "wrong key"], DUMMY_LIST, KeyError),
        ([1, "bar", "wrong key"], DUMMY_LIST, KeyError),
        ([1, "fruits", "index should be int"], DUMMY_LIST, TypeError),
        ([1, "fruits", 100], DUMMY_LIST, IndexError),
    ),
)
def test_seek_with_bad_path(
    yaml_path: list[int | str],
    data: MutableMapping[str, Any] | MutableSequence[Any] | str,
    expected_error: type[Exception],
) -> None:
    """Verify that TransformMixin.seek() propagates errors."""
    with pytest.raises(expected_error):
        TransformMixin.seek(yaml_path, data)


@pytest.mark.parametrize(
    ("yaml_path", "data", "expected"),
    (
        ([], DUMMY_MAP, DUMMY_MAP),
        (["foo"], DUMMY_MAP, DUMMY_MAP["foo"]),
        (["bar"], DUMMY_MAP, DUMMY_MAP["bar"]),
        (["bar", "some"], DUMMY_MAP, DUMMY_MAP["bar"]["some"]),
        (["fruits"], DUMMY_MAP, DUMMY_MAP["fruits"]),
        (["fruits", 0], DUMMY_MAP, DUMMY_MAP["fruits"][0]),
        (["fruits", 1], DUMMY_MAP, DUMMY_MAP["fruits"][1]),
        (["answer"], DUMMY_MAP, DUMMY_MAP["answer"]),
        (["answer", 0], DUMMY_MAP, DUMMY_MAP["answer"][0]),
        (["answer", 0, "forty-two"], DUMMY_MAP, DUMMY_MAP["answer"][0]["forty-two"]),
        (
            ["answer", 0, "forty-two", 0],
            DUMMY_MAP,
            DUMMY_MAP["answer"][0]["forty-two"][0],
        ),
        (
            ["answer", 0, "forty-two", 1],
            DUMMY_MAP,
            DUMMY_MAP["answer"][0]["forty-two"][1],
        ),
        (
            ["answer", 0, "forty-two", 2],
            DUMMY_MAP,
            DUMMY_MAP["answer"][0]["forty-two"][2],
        ),
        ([], DUMMY_LIST, DUMMY_LIST),
        ([0], DUMMY_LIST, DUMMY_LIST[0]),
        ([0, "foo"], DUMMY_LIST, DUMMY_LIST[0]["foo"]),
        ([1], DUMMY_LIST, DUMMY_LIST[1]),
        ([1, "bar"], DUMMY_LIST, DUMMY_LIST[1]["bar"]),
        ([1, "bar", "some"], DUMMY_LIST, DUMMY_LIST[1]["bar"]["some"]),
        ([1, "fruits"], DUMMY_LIST, DUMMY_LIST[1]["fruits"]),
        ([1, "fruits", 0], DUMMY_LIST, DUMMY_LIST[1]["fruits"][0]),
        ([1, "fruits", 1], DUMMY_LIST, DUMMY_LIST[1]["fruits"][1]),
        ([2], DUMMY_LIST, DUMMY_LIST[2]),
        ([2, "answer"], DUMMY_LIST, DUMMY_LIST[2]["answer"]),
        ([2, "answer", 0], DUMMY_LIST, DUMMY_LIST[2]["answer"][0]),
        (
            [2, "answer", 0, "forty-two"],
            DUMMY_LIST,
            DUMMY_LIST[2]["answer"][0]["forty-two"],
        ),
        (
            [2, "answer", 0, "forty-two", 0],
            DUMMY_LIST,
            DUMMY_LIST[2]["answer"][0]["forty-two"][0],
        ),
        (
            [2, "answer", 0, "forty-two", 1],
            DUMMY_LIST,
            DUMMY_LIST[2]["answer"][0]["forty-two"][1],
        ),
        (
            [2, "answer", 0, "forty-two", 2],
            DUMMY_LIST,
            DUMMY_LIST[2]["answer"][0]["forty-two"][2],
        ),
        (
            [],
            "this is a string that should be returned as is, ignoring path.",
            "this is a string that should be returned as is, ignoring path.",
        ),
        (
            [2, "answer", 0, "forty-two", 2],
            "this is a string that should be returned as is, ignoring path.",
            "this is a string that should be returned as is, ignoring path.",
        ),
    ),
)
def test_seek(
    yaml_path: list[int | str],
    data: MutableMapping[str, Any] | MutableSequence[Any] | str,
    expected: Any,
) -> None:
    """Ensure TransformMixin.seek() retrieves the correct data."""
    actual = TransformMixin.seek(yaml_path, data)
    assert actual == expected
