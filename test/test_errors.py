"""Test ansiblelint.errors."""

import pytest

from ansiblelint.errors import MatchError


def test_matcherror() -> None:
    """."""
    match = MatchError("foo", lineno=1, column=2)
    with pytest.raises(TypeError):
        assert match <= 0

    assert match != 0

    assert match.position == "1:2"

    match2 = MatchError("foo", lineno=1)
    assert match2.position == "1"

    # str and repr are for the moment the same
    assert str(match) == repr(match)

    # tests implicit level
    assert match.level == "warning"
