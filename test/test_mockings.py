"""Test mockings module."""
from typing import Any

import pytest

from ansiblelint._mockings import _make_module_stub
from ansiblelint.config import options
from ansiblelint.constants import RC


def test_make_module_stub(mocker: Any) -> None:
    """Test make module stub."""
    mocker.patch("ansiblelint.config.options.cache_dir", return_value=".")
    assert options.cache_dir is not None
    with pytest.raises(SystemExit) as exc:
        _make_module_stub("")
    assert exc.type == SystemExit
    assert exc.value.code == RC.INVALID_CONFIG
