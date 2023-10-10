"""Test mockings module."""

from pathlib import Path

import pytest

from ansiblelint._mockings import _make_module_stub
from ansiblelint.config import Options
from ansiblelint.constants import RC


def test_make_module_stub(config_options: Options) -> None:
    """Test make module stub."""
    config_options.cache_dir = Path()  # current directory
    with pytest.raises(SystemExit) as exc:
        _make_module_stub(module_name="", options=config_options)
    assert exc.type == SystemExit
    assert exc.value.code == RC.INVALID_CONFIG
