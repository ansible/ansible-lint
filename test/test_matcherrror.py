"""Tests for MatchError."""

import operator
from collections.abc import Callable
from typing import Any

import pytest

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules.no_changed_when import CommandHasChangesCheckRule
from ansiblelint.rules.partial_become import BecomeUserWithoutBecomeRule


class DummyTestObject:
    """A dummy object for equality tests."""

    def __repr__(self) -> str:
        """Return a dummy object representation for parametrize."""
        return f"{self.__class__.__name__}()"

    def __eq__(self, other: object) -> bool:
        """Report the equality check failure with any object."""
        return False

    def __ne__(self, other: object) -> bool:
        """Report the confirmation of inequality with any object."""
        return True


class DummySentinelTestObject:
    """A dummy object for equality protocol tests with sentinel."""

    def __eq__(self, other: object) -> bool:
        """Return sentinel as result of equality check w/ anything."""
        return "EQ_SENTINEL"  # type: ignore[return-value]

    def __ne__(self, other: object) -> bool:
        """Return sentinel as result of inequality check w/ anything."""
        return "NE_SENTINEL"  # type: ignore[return-value]

    def __lt__(self, other: object) -> bool:
        """Return sentinel as result of less than check w/ anything."""
        return "LT_SENTINEL"  # type: ignore[return-value]

    def __gt__(self, other: object) -> bool:
        """Return sentinel as result of greater than chk w/ anything."""
        return "GT_SENTINEL"  # type: ignore[return-value]


@pytest.mark.parametrize(
    ("left_match_error", "right_match_error"),
    (
        (MatchError("foo"), MatchError("foo")),
        (MatchError("a", details="foo"), MatchError("a", details="foo")),
    ),
)
def test_matcherror_compare(
    left_match_error: MatchError,
    right_match_error: MatchError,
) -> None:
    """Check that MatchError instances with similar attrs are equivalent."""
    assert left_match_error == right_match_error


def test_matcherror_invalid() -> None:
    """Ensure that MatchError requires message or rule."""
    with pytest.raises(TypeError):
        MatchError()  # pylint: disable=pointless-exception-statement


@pytest.mark.parametrize(
    ("left_match_error", "right_match_error"),
    (
        # sorting by message
        (MatchError("z"), MatchError("a")),
        # filenames takes priority in sorting
        (
            MatchError("a", lintable=Lintable("b", content="")),
            MatchError("a", lintable=Lintable("a", content="")),
        ),
        # rule id partial-become > rule id no-changed-when
        (
            MatchError(rule=BecomeUserWithoutBecomeRule()),
            MatchError(rule=CommandHasChangesCheckRule()),
        ),
        # details are taken into account
        (MatchError("a", details="foo"), MatchError("a", details="bar")),
        # columns are taken into account
        (MatchError("a", column=3), MatchError("a", column=1)),
        (MatchError("a", column=3), MatchError("a")),
    ),
)
class TestMatchErrorCompare:
    """Test the comparison of MatchError instances."""

    @staticmethod
    def test_match_error_less_than(
        left_match_error: MatchError,
        right_match_error: MatchError,
    ) -> None:
        """Check 'less than' protocol implementation in MatchError."""
        assert right_match_error < left_match_error

    @staticmethod
    def test_match_error_greater_than(
        left_match_error: MatchError,
        right_match_error: MatchError,
    ) -> None:
        """Check 'greater than' protocol implementation in MatchError."""
        assert left_match_error > right_match_error

    @staticmethod
    def test_match_error_not_equal(
        left_match_error: MatchError,
        right_match_error: MatchError,
    ) -> None:
        """Check 'not equals' protocol implementation in MatchError."""
        assert left_match_error != right_match_error


@pytest.mark.parametrize(
    "other",
    (
        pytest.param(None, id="none"),
        pytest.param("foo", id="str"),
        pytest.param(42, id="int"),
        pytest.param(Exception("foo"), id="exc"),
    ),
    ids=repr,
)
@pytest.mark.parametrize(
    ("operation", "operator_char"),
    (
        pytest.param(operator.le, "<=", id="le"),
        pytest.param(operator.gt, ">", id="gt"),
    ),
)
def test_matcherror_compare_no_other_fallback(
    other: Any,
    operation: Callable[..., bool],
    operator_char: str,
) -> None:
    """Check that MatchError comparison with other types causes TypeError."""
    expected_error = (
        r"^("
        rf"unsupported operand type\(s\) for {operator_char!s}:|"
        rf"'{operator_char!s}' not supported between instances of"
        rf") 'MatchError' and '{type(other).__name__!s}'$"
    )
    with pytest.raises(TypeError, match=expected_error):
        operation(MatchError("foo"), other)


@pytest.mark.parametrize(
    "other",
    (
        pytest.param(None, id="none"),
        pytest.param("foo", id="str"),
        pytest.param(42, id="int"),
        pytest.param(Exception("foo"), id="exception"),
        pytest.param(DummyTestObject(), id="obj"),
    ),
    ids=repr,
)
@pytest.mark.parametrize(
    ("operation", "expected_value"),
    (
        pytest.param(operator.eq, False, id="eq"),
        pytest.param(operator.ne, True, id="ne"),
    ),
)
def test_matcherror_compare_with_other_fallback(
    other: object,
    operation: Callable[..., bool],
    expected_value: bool,
) -> None:
    """Check that MatchError comparison runs other types fallbacks."""
    assert operation(MatchError(message="foo"), other) is expected_value


@pytest.mark.parametrize(
    ("operation", "expected_value"),
    (
        pytest.param(operator.eq, "EQ_SENTINEL", id="eq"),
        pytest.param(operator.ne, "NE_SENTINEL", id="ne"),
        # NOTE: these are swapped because when we do `x < y`, and `x.__lt__(y)`
        # NOTE: returns `NotImplemented`, Python will reverse the check into
        # NOTE: `y > x`, and so `y.__gt__(x) is called.
        # Ref: https://docs.python.org/3/reference/datamodel.html#object.__lt__
        pytest.param(operator.lt, "GT_SENTINEL", id="gt"),
        pytest.param(operator.gt, "LT_SENTINEL", id="lt"),
    ),
)
def test_matcherror_compare_with_dummy_sentinel(
    operation: Callable[..., bool],
    expected_value: str,
) -> None:
    """Check that MatchError comparison runs other types fallbacks."""
    dummy_obj = DummySentinelTestObject()
    # NOTE: This assertion abuses the CPython property to cache short string
    # NOTE: objects because the identity check is more precise and we don't
    # NOTE: want extra operator protocol methods to influence the test.
    assert operation(MatchError("foo"), dummy_obj) is expected_value  # type: ignore[comparison-overlap]
