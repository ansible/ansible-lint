"""Tests for ansible.cfg collections_paths configuration precedence.

This test module verifies that ansible-lint correctly honors collections_paths
settings from ansible.cfg, fixing the regression reported in issue #4851.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from ansiblelint.app import get_app
from ansiblelint.config import options
from ansiblelint.testing import run_ansible_lint

if TYPE_CHECKING:
    from pytest import MonkeyPatch


def test_ansible_cfg_collections_paths_basic(tmp_path: Path) -> None:
    """Test that collections_paths from ansible.cfg is honored.

    This test reproduces the bug from issue #4851 where collections_paths
    from ansible.cfg was ignored even though other settings were respected.

    The test SHOULD FAIL before the fix and PASS after the fix.
    """
    # Create project structure
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create custom collections directory
    custom_collections = project_dir / "my_collections"
    custom_collections.mkdir()

    # Create ansible.cfg with explicit collections_paths
    ansible_cfg = project_dir / "ansible.cfg"
    ansible_cfg.write_text(
        f"""[defaults]
collections_path = {custom_collections}
collections_scan_sys_path = false
""",
        encoding="utf-8",
    )

    # Create a minimal playbook
    playbook = project_dir / "playbook.yml"
    playbook.write_text(
        """---
- name: Test playbook
  hosts: localhost
  gather_facts: false
  tasks:
    - name: Test task
      ansible.builtin.debug:
        msg: "Hello"
""",
        encoding="utf-8",
    )

    # Run ansible-lint and check that custom collections path is used
    result = run_ansible_lint(
        playbook,
        cwd=project_dir,
        offline=True,
    )

    # The test should not fail with linting errors (we have a valid playbook)
    assert result.returncode == 0, f"Unexpected lint errors: {result.stderr}"

    # Verify the actual collections path was honored by checking what
    # ansible-lint would have set based on the ansible.cfg
    from ansiblelint.ansible_config import read_collections_paths_from_ansible_cfg

    loaded_paths = read_collections_paths_from_ansible_cfg(str(project_dir))
    assert loaded_paths is not None, "collections_paths should be read from ansible.cfg"
    assert any(
        str(custom_collections) in path for path in loaded_paths
    ), f"Custom collections path {custom_collections} not found in {loaded_paths}"


def test_ansible_cfg_collections_paths_colon_separated(tmp_path: Path) -> None:
    """Test that colon-separated collections_paths are parsed correctly."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create multiple custom collections directories
    collections_1 = project_dir / "collections_one"
    collections_2 = project_dir / "collections_two"
    collections_1.mkdir()
    collections_2.mkdir()

    # Create ansible.cfg with multiple paths
    ansible_cfg = project_dir / "ansible.cfg"
    ansible_cfg.write_text(
        f"""[defaults]
collections_path = {collections_1}:{collections_2}
""",
        encoding="utf-8",
    )

    playbook = project_dir / "playbook.yml"
    playbook.write_text(
        """---
- name: Test
  hosts: localhost
  tasks:
    - ansible.builtin.debug:
        msg: test
""",
        encoding="utf-8",
    )

    from ansiblelint.ansible_config import read_collections_paths_from_ansible_cfg

    paths = read_collections_paths_from_ansible_cfg(str(project_dir))

    assert paths is not None, "collections_paths should be read from ansible.cfg"
    assert len(paths) == 2, f"Expected 2 paths, got {len(paths)}: {paths}"
    assert any(
        str(collections_1) in path for path in paths
    ), f"Path {collections_1} not found in {paths}"
    assert any(
        str(collections_2) in path for path in paths
    ), f"Path {collections_2} not found in {paths}"


def test_ansible_cfg_collections_paths_relative(tmp_path: Path) -> None:
    """Test that relative paths in collections_paths are resolved correctly."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Use relative path in ansible.cfg
    ansible_cfg = project_dir / "ansible.cfg"
    ansible_cfg.write_text(
        """[defaults]
collections_path = ./my_collections:../shared_collections
""",
        encoding="utf-8",
    )

    from ansiblelint.ansible_config import read_collections_paths_from_ansible_cfg

    paths = read_collections_paths_from_ansible_cfg(str(project_dir))

    assert paths is not None, "collections_paths should be read from ansible.cfg"
    assert len(paths) == 2, f"Expected 2 paths, got {len(paths)}"

    # Verify paths are absolute (resolved)
    for path in paths:
        assert Path(path).is_absolute(), f"Path {path} should be absolute"


def test_ansible_cfg_missing_collections_paths(tmp_path: Path) -> None:
    """Test that ansible-lint works when collections_paths is not set.

    This ensures backward compatibility - when collections_paths is not
    explicitly configured, ansible-lint should use Runtime's defaults.
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create ansible.cfg WITHOUT collections_paths
    ansible_cfg = project_dir / "ansible.cfg"
    ansible_cfg.write_text(
        """[defaults]
# No collections_paths setting
host_key_checking = false
""",
        encoding="utf-8",
    )

    from ansiblelint.ansible_config import read_collections_paths_from_ansible_cfg

    paths = read_collections_paths_from_ansible_cfg(str(project_dir))

    # Should return None when not configured (preserves default behavior)
    assert (
        paths is None
    ), "When collections_paths is not set, function should return None"


def test_ansible_cfg_env_var_precedence(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Test that ANSIBLE_COLLECTIONS_PATH env var is honored when set explicitly.

    According to Ansible's precedence rules:
    1. Environment variable takes highest precedence
    2. ansible.cfg setting
    3. Defaults

    This test verifies the environment variable wins when explicitly set.
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    env_collections = tmp_path / "env_collections"
    env_collections.mkdir()

    cfg_collections = project_dir / "cfg_collections"
    cfg_collections.mkdir()

    # Set environment variable
    monkeypatch.setenv("ANSIBLE_COLLECTIONS_PATH", str(env_collections))

    # Also set in ansible.cfg (should be overridden by env var)
    ansible_cfg = project_dir / "ansible.cfg"
    ansible_cfg.write_text(
        f"""[defaults]
collections_path = {cfg_collections}
""",
        encoding="utf-8",
    )

    playbook = project_dir / "playbook.yml"
    playbook.write_text(
        """---
- name: Test
  hosts: localhost
  tasks:
    - ansible.builtin.debug:
        msg: test
""",
        encoding="utf-8",
    )

    # When env var is already set, our code should NOT override it
    # We test this by creating a new App with the test project_dir
    from ansiblelint.config import Options
    from ansiblelint.app import App

    test_options = Options(project_dir=str(project_dir))
    
    # Before creating app, verify env var is set
    assert os.environ.get("ANSIBLE_COLLECTIONS_PATH") == str(env_collections)
    
    # Create app (should preserve ENV VAR, not override with ansible.cfg)
    test_app = App(options=test_options)
    
    # Environment variable should still be set to env_collections
    current_env = os.environ.get("ANSIBLE_COLLECTIONS_PATH", "")
    assert (
        str(env_collections) in current_env
    ), f"Environment variable should be preserved when explicitly set, got: {current_env}"


def test_ansible_cfg_not_found(tmp_path: Path) -> None:
    """Test behavior when ansible.cfg doesn't exist.

    Should gracefully handle missing ansible.cfg and use defaults.
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # No ansible.cfg created

    from ansiblelint.ansible_config import read_collections_paths_from_ansible_cfg

    paths = read_collections_paths_from_ansible_cfg(str(project_dir))

    # Should return None gracefully
    assert paths is None, "Should return None when ansible.cfg doesn't exist"


def test_ansible_cfg_collections_paths_alternate_key(tmp_path: Path) -> None:
    """Test that both 'collections_path' and 'collections_paths' keys work.

    Ansible accepts both forms, so ansible-lint should too.
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    custom_collections = project_dir / "my_collections"
    custom_collections.mkdir()

    # Use 'collections_paths' (with 's') instead of 'collections_path'
    ansible_cfg = project_dir / "ansible.cfg"
    ansible_cfg.write_text(
        f"""[defaults]
collections_paths = {custom_collections}
""",
        encoding="utf-8",
    )

    from ansiblelint.ansible_config import read_collections_paths_from_ansible_cfg

    paths = read_collections_paths_from_ansible_cfg(str(project_dir))

    assert paths is not None, "Should read 'collections_paths' key"
    assert any(
        str(custom_collections) in path for path in paths
    ), f"Custom path {custom_collections} not found in {paths}"


@pytest.mark.parametrize(
    ("config_content", "expected_count"),
    [
        pytest.param(
            "[defaults]\ncollections_path = /path/one:/path/two:/path/three",
            3,
            id="three_paths",
        ),
        pytest.param(
            "[defaults]\ncollections_path = /single/path",
            1,
            id="single_path",
        ),
        pytest.param(
            "[defaults]\ncollections_path = /path/one : /path/two",
            2,
            id="spaces_around_colon",
        ),
    ],
)
def test_ansible_cfg_path_parsing(
    tmp_path: Path,
    config_content: str,
    expected_count: int,
) -> None:
    """Test various formats of collections_path parsing."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    ansible_cfg = project_dir / "ansible.cfg"
    ansible_cfg.write_text(config_content, encoding="utf-8")

    from ansiblelint.ansible_config import read_collections_paths_from_ansible_cfg

    paths = read_collections_paths_from_ansible_cfg(str(project_dir))

    assert paths is not None, f"Should parse config: {config_content}"
    assert (
        len(paths) == expected_count
    ), f"Expected {expected_count} paths, got {len(paths)}: {paths}"
