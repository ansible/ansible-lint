"""Test mockings module."""

from pathlib import Path

import pytest

from ansiblelint._mockings import _make_module_stub
from ansiblelint.config import Options
from ansiblelint.constants import RC
from ansiblelint.testing import run_ansible_lint


def test_make_module_stub(config_options: Options) -> None:
    """Test make module stub."""
    config_options.cache_dir = Path()  # current directory
    with pytest.raises(SystemExit) as exc:
        _make_module_stub(module_name="", options=config_options)
    assert exc.type is SystemExit
    assert exc.value.code == RC.INVALID_CONFIG


def test_mock_roles_with_collection_name(tmp_path: Path) -> None:
    """Test mock_roles with collection role names (namespace.collection.role).

    See https://github.com/ansible/ansible-lint/issues/4973
    """
    (tmp_path / ".ansible-lint.yml").write_text("mock_roles:\n  - ns.coll.role\n")
    (tmp_path / "playbook.yml").write_text(
        "---\n- name: Test\n  hosts: localhost\n  roles:\n    - ns.coll.role\n"
    )
    result = run_ansible_lint("playbook.yml", cwd=tmp_path, offline=False)
    assert "was not found" not in result.stdout
