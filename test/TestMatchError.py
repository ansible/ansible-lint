"""Tests for MatchError."""

import operator

from ansiblelint.errors import MatchError
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.rules.AlwaysRunRule import AlwaysRunRule
from ansiblelint.rules.BecomeUserWithoutBecomeRule import BecomeUserWithoutBecomeRule

import pytest


@pytest.mark.parametrize(
    ('left_match_error', 'right_match_error'),
    (
        (MatchError("foo"), MatchError("foo")),
        # `line` is ignored in comparisions, even when it differs:
        (MatchError("a", line={}), MatchError("a", line={"a": "b"})),
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
        # line will not be taken into account
        (MatchError("b", line={}), MatchError("a", line={"a": "b"})),
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
)
@pytest.mark.parametrize(
    'operation',
    (
        operator.eq,
        operator.ne,
        operator.le,
        operator.gt,
    ),
    ids=['eq', 'ne', 'le', 'gt']
)
def test_matcherror_compare_invalid(other, operation):
    """Check that MatchError comparison with other types raises."""
    with pytest.raises(NotImplementedError):
        operation(MatchError("foo"), other)
