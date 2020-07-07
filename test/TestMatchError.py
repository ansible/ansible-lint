from ansiblelint.errors import MatchError
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.rules.AlwaysRunRule import AlwaysRunRule
from ansiblelint.rules.BecomeUserWithoutBecomeRule import BecomeUserWithoutBecomeRule

import pytest


def test_matcherror_compare():
    assert MatchError("foo") == MatchError("foo")


class AnsibleLintRuleWithStringId(AnsibleLintRule):
    id = "200"


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
def test_matcherror_sort(a, b):
    assert b < a
    assert a > b
    assert a != b


def test_matcherror_invalid():
    """Ensure that MatchError requires message or rule."""
    expected_err = "^MatchError() missing a required argument: one of 'message' or 'rule'$"
    with pytest.raises(TypeError, match=expected_err):
        MatchError()
