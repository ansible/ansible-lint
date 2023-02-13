"""Tests for loaders submodule."""
from ansiblelint.loaders import load_ignore_txt


def test_load_ignore_txt() -> None:
    """Test load_ignore_txt."""
    result = load_ignore_txt(".ansible-lint-ignore")
    assert result == {"playbook2.yml": {"foo-bar", "package-latest"}}
