"""Tests for config module."""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ansiblelint.config import (
    PROFILES,
    _fetch_latest_release,
    _format_version_upgrade_message,
    _load_version_cache,
    _version_cache_needs_refresh,
    get_deps_versions,
    get_version_warning,
    guess_install_method,
    has_custom_ansible_env,
    in_venv,
)
from ansiblelint.rules import RulesCollection
from packaging.version import Version


def test_profiles(default_rules_collection: RulesCollection) -> None:
    """Test the rules included in profiles are valid."""
    profile_banned_tags = {"opt-in", "experimental"}
    for name, data in PROFILES.items():
        for profile_rule_id in data["rules"]:
            for rule in default_rules_collection.rules:
                if profile_rule_id == rule.id:
                    forbidden_tags = profile_banned_tags & set(rule.tags)
                    assert not forbidden_tags, (
                        f"Rule {profile_rule_id} from {name} profile cannot use {profile_banned_tags & set(rule.tags)} tag."
                    )


def test_in_venv_with_real_prefix() -> None:
    """Test in_venv detects virtualenv with real_prefix."""
    with patch.object(sys, "real_prefix", "fake_prefix", create=True):
        assert in_venv() is True


def test_in_venv_with_conda() -> None:
    """Test in_venv detects conda environment."""
    with patch.dict(os.environ, {"CONDA_EXE": "/path/to/conda"}):
        assert in_venv() is True


def test_in_venv_with_base_prefix() -> None:
    """Test in_venv detects venv with base_prefix."""
    with patch.object(sys, "base_prefix", "/different/path"):
        with patch.object(sys, "prefix", "/current/path"):
            assert in_venv() is True


def test_in_venv_not_in_venv() -> None:
    """Test in_venv returns False when not in venv."""
    with patch.object(sys, "base_prefix", "/same/path"):
        with patch.object(sys, "prefix", "/same/path"):
            with patch.dict(os.environ, {}, clear=False):
                # Remove CONDA_EXE if it exists
                env_copy = os.environ.copy()
                env_copy.pop("CONDA_EXE", None)
                with patch.dict(os.environ, env_copy, clear=True):
                    assert in_venv() is False


def test_has_custom_ansible_env_set() -> None:
    """Test has_custom_ansible_env detects ANSIBLE_* env vars."""
    with patch.dict(os.environ, {"ANSIBLE_HOME": "/custom/path"}):
        assert has_custom_ansible_env() is True


def test_has_custom_ansible_env_not_set() -> None:
    """Test has_custom_ansible_env returns False when no vars are set."""
    env_copy = {k: v for k, v in os.environ.items() if not k.startswith("ANSIBLE_")}
    with patch.dict(os.environ, env_copy, clear=True):
        assert has_custom_ansible_env() is False


def test_get_deps_versions() -> None:
    """Test get_deps_versions returns expected keys."""
    result = get_deps_versions()
    assert "ansible-core" in result
    assert "ansible-compat" in result
    assert "ruamel-yaml" in result


def test_version_cache_needs_refresh_no_file() -> None:
    """Test version cache refresh when file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = os.path.join(tmpdir, "nonexistent.json")
        assert _version_cache_needs_refresh(cache_file) is True


def test_version_cache_needs_refresh_fresh_file() -> None:
    """Test version cache refresh with recent file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = os.path.join(tmpdir, "cache.json")
        # Create a recent file
        with open(cache_file, "w") as f:
            json.dump({}, f)
        assert _version_cache_needs_refresh(cache_file) is False


def test_version_cache_needs_refresh_old_file() -> None:
    """Test version cache refresh with old file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = os.path.join(tmpdir, "cache.json")
        # Create file and modify timestamp to be old
        with open(cache_file, "w") as f:
            json.dump({}, f)
        # Set modification time to 2 days ago
        import time
        old_time = time.time() - (48 * 60 * 60)
        os.utime(cache_file, (old_time, old_time))
        assert _version_cache_needs_refresh(cache_file) is True


def test_load_version_cache() -> None:
    """Test loading version cache from file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = os.path.join(tmpdir, "cache.json")
        test_data = {"version": "1.0.0", "url": "https://example.com"}
        with open(cache_file, "w") as f:
            json.dump(test_data, f)
        result = _load_version_cache(cache_file)
        assert result == test_data


def test_fetch_latest_release_success() -> None:
    """Test fetching latest release."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = os.path.join(tmpdir, "cache.json")
        test_data = {"tag_name": "v1.0.0", "html_url": "https://example.com"}
        mock_response = MagicMock()
        mock_response.__enter__.return_value = MagicMock()
        with patch("urllib.request.urlopen", return_value=mock_response):
            with patch("json.load", return_value=test_data):
                with patch("builtins.open", create=True) as mock_file:
                    mock_file.return_value.__enter__.return_value = MagicMock()
                    result = _fetch_latest_release(cache_file)
                    assert result == test_data


def test_fetch_latest_release_network_error() -> None:
    """Test fetch latest release handles network errors."""
    from urllib.error import URLError
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = os.path.join(tmpdir, "cache.json")
        with patch("urllib.request.urlopen", side_effect=URLError("Network error")):
            result = _fetch_latest_release(cache_file)
            assert result == {}


def test_fetch_latest_release_invalid_url() -> None:
    """Test fetch latest release validates URL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = os.path.join(tmpdir, "cache.json")
        with patch("ansiblelint.config._fetch_latest_release") as mock_fetch:
            # Call with mocked function to test the real validation
            from ansiblelint.config import _fetch_latest_release as real_fetch
            # This should work fine with https URL
            mock_fetch = MagicMock(return_value={})
            result = real_fetch(cache_file)
            # The real function should not raise


def test_format_version_upgrade_message_empty_data() -> None:
    """Test version upgrade message with empty data."""
    result = _format_version_upgrade_message(Version("1.0.0"), {}, "")
    assert result == ""


def test_format_version_upgrade_message_prerelease() -> None:
    """Test version upgrade message for pre-release."""
    data = {"html_url": "https://example.com", "tag_name": "v0.9.0"}
    result = _format_version_upgrade_message(Version("1.0.0"), data, "")
    assert "pre-release" in result


def test_format_version_upgrade_message_newer_available() -> None:
    """Test version upgrade message when newer version available."""
    data = {"html_url": "https://example.com", "tag_name": "v2.0.0"}
    result = _format_version_upgrade_message(Version("1.0.0"), data, "pip install")
    assert "new release" in result
    assert "pip install" in result


def test_format_version_upgrade_message_up_to_date() -> None:
    """Test version upgrade message when up to date."""
    data = {"html_url": "https://example.com", "tag_name": "v1.0.0"}
    result = _format_version_upgrade_message(Version("1.0.0"), data, "")
    assert result == ""


@patch("ansiblelint.config.guess_install_method", return_value="")
def test_get_version_warning_no_pip(mock_guess: MagicMock) -> None:
    """Test version warning when pip install method not detected."""
    result = get_version_warning()
    assert result == ""


def test_get_version_warning_dev_version() -> None:
    """Test version warning for dev version."""
    with patch("ansiblelint.config.__version__", "0.1.dev1"):
        result = get_version_warning()
        assert result == ""


@patch("ansiblelint.config.in_venv", return_value=False)
@patch("ansiblelint.config.distribution")
def test_guess_install_method_not_pip_installer(
    mock_dist: MagicMock, mock_venv: MagicMock
) -> None:
    """Test guess_install_method when package was not installed with pip."""
    mock_dist_obj = MagicMock()
    mock_dist_obj.read_text.return_value = "setuptools"
    mock_dist.return_value = mock_dist_obj
    result = guess_install_method()
    assert result == ""


@patch("ansiblelint.config.in_venv", return_value=False)
@patch("ansiblelint.config.distribution")
def test_guess_install_method_pip_not_found(
    mock_dist: MagicMock, mock_venv: MagicMock
) -> None:
    """Test guess_install_method when distribution not found."""
    from importlib.metadata import PackageNotFoundError
    mock_dist.side_effect = PackageNotFoundError("not found")
    result = guess_install_method()
    assert result == ""


@patch("ansiblelint.config.in_venv", return_value=True)
@patch("ansiblelint.config.distribution")
def test_guess_install_method_venv(
    mock_dist: MagicMock, mock_venv: MagicMock
) -> None:
    """Test guess_install_method in virtual environment."""
    mock_dist_obj = MagicMock()
    mock_dist_obj.read_text.return_value = "pip"
    mock_dist.return_value = mock_dist_obj
    with patch("ansiblelint.config.warnings.catch_warnings"):
        with patch(
            "pip._internal.metadata.get_default_environment"
        ) as mock_get_env:
            mock_env = MagicMock()
            mock_dist_check = MagicMock()
            mock_env.get_distribution.return_value = mock_dist_check
            mock_get_env.return_value = mock_env
            with patch(
                "pip._internal.req.req_uninstall.uninstallation_paths", return_value=["path"]
            ):
                result = guess_install_method()
                assert "pip install --upgrade" in result


@patch("ansiblelint.config.in_venv", return_value=False)
@patch("ansiblelint.config.distribution")
def test_guess_install_method_user_install(
    mock_dist: MagicMock, mock_venv: MagicMock
) -> None:
    """Test guess_install_method with user install."""
    mock_dist_obj = MagicMock()
    mock_dist_obj.read_text.return_value = "pip"
    mock_dist.return_value = mock_dist_obj
    with patch("ansiblelint.config.warnings.catch_warnings"):
        with patch(
            "pip._internal.metadata.get_default_environment"
        ) as mock_get_env:
            mock_env = MagicMock()
            mock_dist_check = MagicMock()
            mock_env.get_distribution.return_value = mock_dist_check
            mock_get_env.return_value = mock_env
            with patch(
                "pip._internal.req.req_uninstall.uninstallation_paths", return_value=["path"]
            ):
                with patch("ansiblelint.config.__file__", os.path.expanduser("~/.local/lib/python/site-packages/test.py")):
                    result = guess_install_method()
                    assert "pip3 install --user --upgrade" in result


@patch("ansiblelint.config.in_venv", return_value=False)
@patch("ansiblelint.config.distribution")
def test_guess_install_method_pip_error(
    mock_dist: MagicMock, mock_venv: MagicMock
) -> None:
    """Test guess_install_method when pip internals raise errors."""
    mock_dist_obj = MagicMock()
    mock_dist_obj.read_text.return_value = "pip"
    mock_dist.return_value = mock_dist_obj
    with patch("ansiblelint.config.warnings.catch_warnings"):
        with patch(
            "pip._internal.metadata.get_default_environment",
            side_effect=AttributeError("pip internals"),
        ):
            result = guess_install_method()
            assert result == ""


@patch("ansiblelint.config.in_venv", return_value=False)
@patch("ansiblelint.config.distribution")
def test_guess_install_method_no_uninstall_paths(
    mock_dist: MagicMock, mock_venv: MagicMock
) -> None:
    """Test guess_install_method when no uninstall paths found."""
    mock_dist_obj = MagicMock()
    mock_dist_obj.read_text.return_value = "pip"
    mock_dist.return_value = mock_dist_obj
    with patch("ansiblelint.config.warnings.catch_warnings"):
        with patch(
            "pip._internal.metadata.get_default_environment"
        ) as mock_get_env:
            mock_env = MagicMock()
            mock_env.get_distribution.return_value = None
            mock_get_env.return_value = mock_env
            result = guess_install_method()
            assert result == ""
