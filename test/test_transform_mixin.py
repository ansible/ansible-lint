"""Tests for TransformMixin."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ansiblelint.rules import TransformMixin

if TYPE_CHECKING:
    from collections.abc import MutableMapping, MutableSequence
    from typing import Any


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
        pytest.param([], DUMMY_MAP, DUMMY_MAP, id="0"),
        pytest.param(["foo"], DUMMY_MAP, DUMMY_MAP["foo"], id="1"),
        pytest.param(["bar"], DUMMY_MAP, DUMMY_MAP["bar"], id="2"),
        pytest.param(["bar", "some"], DUMMY_MAP, DUMMY_MAP["bar"]["some"], id="3"),
        pytest.param(["fruits"], DUMMY_MAP, DUMMY_MAP["fruits"], id="4"),
        pytest.param(["fruits", 0], DUMMY_MAP, DUMMY_MAP["fruits"][0], id="5"),
        pytest.param(["fruits", 1], DUMMY_MAP, DUMMY_MAP["fruits"][1], id="6"),
        pytest.param(["answer"], DUMMY_MAP, DUMMY_MAP["answer"], id="7"),
        pytest.param(["answer", 0], DUMMY_MAP, DUMMY_MAP["answer"][0], id="8"),
        pytest.param(
            ["answer", 0, "forty-two"],
            DUMMY_MAP,
            DUMMY_MAP["answer"][0]["forty-two"],
            id="9",
        ),
        pytest.param(
            ["answer", 0, "forty-two", 0],
            DUMMY_MAP,
            DUMMY_MAP["answer"][0]["forty-two"][0],
            id="10",
        ),
        pytest.param(
            ["answer", 0, "forty-two", 1],
            DUMMY_MAP,
            DUMMY_MAP["answer"][0]["forty-two"][1],
            id="11",
        ),
        pytest.param(
            ["answer", 0, "forty-two", 2],
            DUMMY_MAP,
            DUMMY_MAP["answer"][0]["forty-two"][2],
            id="12",
        ),
        pytest.param([], DUMMY_LIST, DUMMY_LIST, id="13"),
        pytest.param([0], DUMMY_LIST, DUMMY_LIST[0], id="14"),
        pytest.param([0, "foo"], DUMMY_LIST, DUMMY_LIST[0]["foo"], id="15"),
        pytest.param([1], DUMMY_LIST, DUMMY_LIST[1], id="16"),
        pytest.param([1, "bar"], DUMMY_LIST, DUMMY_LIST[1]["bar"], id="17"),
        pytest.param(
            [1, "bar", "some"],
            DUMMY_LIST,
            DUMMY_LIST[1]["bar"]["some"],
            id="18",
        ),
        pytest.param([1, "fruits"], DUMMY_LIST, DUMMY_LIST[1]["fruits"], id="19"),
        pytest.param([1, "fruits", 0], DUMMY_LIST, DUMMY_LIST[1]["fruits"][0], id="20"),
        pytest.param([1, "fruits", 1], DUMMY_LIST, DUMMY_LIST[1]["fruits"][1], id="21"),
        pytest.param([2], DUMMY_LIST, DUMMY_LIST[2], id="22"),
        pytest.param([2, "answer"], DUMMY_LIST, DUMMY_LIST[2]["answer"], id="23"),
        pytest.param([2, "answer", 0], DUMMY_LIST, DUMMY_LIST[2]["answer"][0], id="24"),
        pytest.param(
            [2, "answer", 0, "forty-two"],
            DUMMY_LIST,
            DUMMY_LIST[2]["answer"][0]["forty-two"],
            id="25",
        ),
        pytest.param(
            [2, "answer", 0, "forty-two", 0],
            DUMMY_LIST,
            DUMMY_LIST[2]["answer"][0]["forty-two"][0],
            id="26",
        ),
        pytest.param(
            [2, "answer", 0, "forty-two", 1],
            DUMMY_LIST,
            DUMMY_LIST[2]["answer"][0]["forty-two"][1],
            id="27",
        ),
        pytest.param(
            [2, "answer", 0, "forty-two", 2],
            DUMMY_LIST,
            DUMMY_LIST[2]["answer"][0]["forty-two"][2],
            id="28",
        ),
        pytest.param(
            [],
            "this is a string that should be returned as is, ignoring path.",
            "this is a string that should be returned as is, ignoring path.",
            id="29",
        ),
        pytest.param(
            [2, "answer", 0, "forty-two", 2],
            "this is a string that should be returned as is, ignoring path.",
            "this is a string that should be returned as is, ignoring path.",
            id="30",
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
