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


def test_add_collections_path_if_needed(tmp_path: Path) -> None:
    """Test _add_collections_path_if_needed helper."""
    from ansiblelint.app import _add_collections_path_if_needed

    options = Options()
    options.cache_dir = tmp_path
    options.mock_roles = ["ns.coll.role"]
    paths: list[str] = []

    _add_collections_path_if_needed(options, paths)
    assert str(tmp_path / "collections") in paths

    _add_collections_path_if_needed(options, paths)
    assert paths.count(str(tmp_path / "collections")) == 1

    options.mock_roles = ["simple"]
    paths2: list[str] = []
    _add_collections_path_if_needed(options, paths2)
    assert not paths2


def test_options_collection_mocks() -> None:
    """Test Options.has_collection_mocks and mock_collections_path."""
    opts = Options()
    opts.cache_dir = None
    assert opts.mock_collections_path is None

    opts.mock_modules = ["ns.coll.mod"]
    assert opts.has_collection_mocks() is True
