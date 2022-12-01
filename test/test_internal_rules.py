"""Tests for internal rules."""
from ansiblelint._internal.rules import BaseRule


def test_base_rule_url() -> None:
    """Test that rule URL is set to expected value."""
    rule = BaseRule()
    assert rule.url == "https://ansible-lint.readthedocs.io/rules/"
