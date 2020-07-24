"""Tests for MatchError."""

import operator

import pytest

from ansiblelint.errors import MatchError
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.rules.AlwaysRunRule import AlwaysRunRule
from ansiblelint.rules.BecomeUserWithoutBecomeRule import BecomeUserWithoutBecomeRule


class DummyTestObject:
    """A dummy object for equality tests."""

    def __repr__(self):
        """Return a dummy object representation for parmetrize."""
        return '{self.__class__.__name__}()'.format(self=self)

    def __eq__(self, other):
        """Report the equality check failure with any object."""
        return False

    def __ne__(self, other):
        """Report the confirmation of inequality with any object."""
        return True


class DummySentinelTestObject:
    """A dummy object for equality protocol tests with sentinel."""

    def __eq__(self, other):
        """Return sentinel as result of equality check w/ anything."""
        return 'EQ_SENTINEL'

    def __ne__(self, other):
        """Return sentinel as result of inequality check w/ anything."""
        return 'NE_SENTINEL'

    def __lt__(self, other):
        """Return sentinel as result of less than check w/ anything."""
        return 'LT_SENTINEL'

    def __gt__(self, other):
        """Return sentinel as result of greater than chk w/ anything."""
        return 'GT_SENTINEL'


@pytest.mark.parametrize(
    ('left_match_error', 'right_match_error'),
    (
        (MatchError("foo"), MatchError("foo")),
        (MatchError("a", details="foo"), MatchError("a", details="foo")),
    ),
)
def test_matcherror_compare(left_match_error, right_match_error):
    """Check that MatchError instances with similar attrs are equivalent."""
    assert left_match_error == right_match_error


class AnsibleLintRuleWithStringId(AnsibleLintRule):
    id = "ANSIBLE200"


def test_matcherror_invalid():
    """Ensure that MatchError requires message or rule."""
    expected_err = r"^MatchError\(\) missing a required argument: one of 'message' or 'rule'$"
    with pytest.raises(TypeError, match=expected_err):
        MatchError()


@pytest.mark.parametrize(
    ('left_match_error', 'right_match_error'), (
        # sorting by message
        (MatchError("z"), MatchError("a")),
        # filenames takes priority in sorting
        (MatchError("a", filename="b"), MatchError("a", filename="a")),
        # rule id 501 > rule id 101
        (MatchError(rule=BecomeUserWithoutBecomeRule), MatchError(rule=AlwaysRunRule)),
        # rule id "200" > rule id 101
        (MatchError(rule=AnsibleLintRuleWithStringId), MatchError(rule=AlwaysRunRule)),
        # details are taken into account
        (MatchError("a", details="foo"), MatchError("a", details="bar")),
    ))
class TestMatchErrorCompare:

    def test_match_error_less_than(self, left_match_error, right_match_error):
        """Check 'less than' protocol implementation in MatchError."""
        assert right_match_error < left_match_error

    def test_match_error_greater_than(self, left_match_error, right_match_error):
        """Check 'greater than' protocol implementation in MatchError."""
        assert left_match_error > right_match_error

    def test_match_error_not_equal(self, left_match_error, right_match_error):
        """Check 'not equals' protocol implementation in MatchError."""
        assert left_match_error != right_match_error


@pytest.mark.parametrize(
    'other',
    (
        None,
        "foo",
        42,
        Exception("foo"),
    ),
    ids=repr,
)
@pytest.mark.parametrize(
    ('operation', 'operator_char'),
    (
        pytest.param(operator.le, '<=', id='<='),
        pytest.param(operator.gt, '>', id='>'),
    ),
)
def test_matcherror_compare_no_other_fallback(other, operation, operator_char):
    """Check that MatchError comparison with other types causes TypeError."""
    expected_error = (
        r'^('
        r'unsupported operand type\(s\) for {operator!s}:|'
        r"'{operator!s}' not supported between instances of"
        r") 'MatchError' and '{other_type!s}'$".
        format(other_type=type(other).__name__, operator=operator_char)
    )
    with pytest.raises(TypeError, match=expected_error):
        operation(MatchError("foo"), other)


@pytest.mark.parametrize(
    'other',
    (
        None,
        'foo',
        42,
        Exception('foo'),
        DummyTestObject(),
    ),
    ids=repr,
)
@pytest.mark.parametrize(
    ('operation', 'expected_value'),
    (
        (operator.eq, False),
        (operator.ne, True),
    ),
    ids=('==', '!=')
)
def test_matcherror_compare_with_other_fallback(
        other,
        operation,
        expected_value,
):
    """Check that MatchError comparison runs other types fallbacks."""
    assert operation(MatchError("foo"), other) is expected_value


@pytest.mark.parametrize(
    ('operation', 'expected_value'),
    (
        (operator.eq, 'EQ_SENTINEL'),
        (operator.ne, 'NE_SENTINEL'),
        # NOTE: these are swapped because when we do `x < y`, and `x.__lt__(y)`
        # NOTE: returns `NotImplemented`, Python will reverse the check into
        # NOTE: `y > x`, and so `y.__gt__(x) is called.
        # Ref: https://docs.python.org/3/reference/datamodel.html#object.__lt__
        (operator.lt, 'GT_SENTINEL'),
        (operator.gt, 'LT_SENTINEL'),
    ),
    ids=('==', '!=', '<', '>'),
)
def test_matcherror_compare_with_dummy_sentinel(operation, expected_value):
    """Check that MatchError comparison runs other types fallbacks."""
    dummy_obj = DummySentinelTestObject()
    # NOTE: This assertion abuses the CPython property to cache short string
    # NOTE: objects because the identity check is more presice and we don't
    # NOTE: want extra operator protocol methods to influence the test.
    assert operation(MatchError("foo"), dummy_obj) is expected_value
