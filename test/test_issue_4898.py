"""Tests for issue #4898: Silent configuration errors when log_path is set."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from ansiblelint import cli


def test_config_error_with_log_path(tmp_path: Path) -> None:
    """Verify that configuration errors are printed to stderr even with log_path."""
    # 1. Setup temporary paths
    ansible_cfg = tmp_path / "ansible.cfg"
    lint_cfg = tmp_path / ".ansible-lint"
    log_file = tmp_path / "ansible-lint.log"

    # 2. Create ansible.cfg with log_path
    ansible_cfg.write_text(f"[defaults]\nlog_path={log_file}\n")

    # 3. Create invalid .ansible-lint
    lint_cfg.write_text("invalid_option: true\n")

    # 4. Run cli.get_config and verify console_stderr.print was called
    os.environ["ANSIBLE_CONFIG"] = str(ansible_cfg)

    try:
        with (
            patch(
                "ansiblelint.cli.console_stderr.print",
            ) as mock_print,
            pytest.raises(SystemExit) as exc,
        ):
            cli.get_config(["-c", str(lint_cfg)])

        assert exc.value.code == 3

        # 5. Verify console_stderr.print was called with error message
        mock_print.assert_called()
        args, _ = mock_print.call_args
        assert "Invalid configuration file" in args[0]
        assert "invalid_option" in args[0]
    finally:
        os.environ.pop("ANSIBLE_CONFIG", None)


def test_missing_config_error_with_log_path(tmp_path: Path) -> None:
    """Verify that missing configuration file errors are printed to stderr even with log_path."""
    ansible_cfg = tmp_path / "ansible.cfg"
    log_file = tmp_path / "ansible-lint.log"
    missing_cfg = tmp_path / "non-existent.yml"

    ansible_cfg.write_text(f"[defaults]\nlog_path={log_file}\n")
    os.environ["ANSIBLE_CONFIG"] = str(ansible_cfg)

    try:
        with (
            patch(
                "ansiblelint.cli.console_stderr.print",
            ) as mock_print,
            pytest.raises(SystemExit) as exc,
        ):
            cli.get_config(["-c", str(missing_cfg)])

        assert exc.value.code == 3

        mock_print.assert_called()
        args, _ = mock_print.call_args
        assert "Config file not found" in args[0]
    finally:
        os.environ.pop("ANSIBLE_CONFIG", None)
