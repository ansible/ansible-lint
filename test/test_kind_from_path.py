"""Tests for kind_from_path behavior with Python files."""

from pathlib import Path

from ansiblelint.file_utils import kind_from_path


def test_kind_from_path_python_basic() -> None:
    """Ensure Python files are not treated as YAML."""
    p = Path("example.py")

    assert kind_from_path(p, base=False) != "yaml"


def test_kind_from_path_mock_module() -> None:
    """Ensure mock module paths are not treated as YAML."""
    p = Path(".ansible/collections/ansible_collections/x/y/plugins/modules/test.py")

    assert kind_from_path(p, base=False) != "yaml"
