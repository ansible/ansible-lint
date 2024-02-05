"""Tests for constants module."""

from ansiblelint.constants import States


def test_states() -> None:
    """Test that states are evaluated as boolean false."""
    assert bool(States.NOT_LOADED) is False
    assert bool(States.LOAD_FAILED) is False
    assert bool(States.UNKNOWN_DATA) is False
