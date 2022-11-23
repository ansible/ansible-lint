"""Test schemas modules."""
from ansiblelint.schemas import refresh_schemas


def test_refresh_schemas_skip() -> None:
    """Test for schema update skip."""
    assert refresh_schemas(min_age_seconds=0) == 0


def test_refresh_schemas_forced() -> None:
    """Test for forced refresh."""
    assert refresh_schemas(min_age_seconds=3600 * 24 * 365 * 10) == 1
