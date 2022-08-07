"""Tests for ._mockings submodule."""
import pytest

from ansiblelint._mockings import _perform_mockings

from .conftest import cwd


def test_mockings_invalid() -> None:
    """Checks we raise error with invalid galaxy.yml file."""
    with cwd("test/fixtures/invalid-mocking"):
        with pytest.raises(RuntimeError, match="Invalid"):
            _perform_mockings()
