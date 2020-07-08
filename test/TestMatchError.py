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
    ('a', 'b'), (
        # sorting by message
        (MatchError("z"), MatchError("a")),
        # filenames takes priority in sorting
        (MatchError("a", filename="b"), MatchError("a", filename="a")),
        # rule id 501 > rule id 101
        (MatchError(rule=BecomeUserWithoutBecomeRule), MatchError(rule=AlwaysRunRule)),
        # rule id "200" > rule id 101
        (MatchError(rule=AnsibleLintRuleWithStringId), MatchError(rule=AlwaysRunRule))
    ))
class TestMatchErrorCompare:

    def test_lt(self, a, b):
        assert b < a

    def test_gt(self, a, b):
        assert a > b

    def test_ne(self, a, b):
        assert a != b
