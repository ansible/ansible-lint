"""Test mockings module."""
import pytest

from ansiblelint._mockings import _make_module_stub
from ansiblelint.constants import INVALID_CONFIG_RC


def test_make_module_stub() -> None:
    """Test make module stub."""
    with pytest.raises(SystemExit) as exc:
        _make_module_stub("")
    assert exc.type == SystemExit
    assert exc.value.code == INVALID_CONFIG_RC
