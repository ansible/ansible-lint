"""Validate ansiblelint.skip_utils."""
import pytest

from ansiblelint.skip_utils import get_rule_skips_from_line


@pytest.mark.parametrize(
    ("line", "expected"),
    (
        ("foo # noqa: bar", "bar"),
        ("foo # noqa bar", "bar"),
    ),
)
def test_get_rule_skips_from_line(line: str, expected: str) -> None:
    """Validate get_rule_skips_from_line."""
    x = get_rule_skips_from_line(line)
    assert x == [expected]
