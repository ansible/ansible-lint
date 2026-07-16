"""Tests for issue #4898: Silent configuration errors when log_path is set."""

import logging
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from ansiblelint import cli


def test_config_error_with_log_path(tmp_path: Path) -> None:
    """Verify that configuration errors are printed to stderr and logged to log_path."""
    # 1. Setup temporary paths
    ansible_cfg = tmp_path / "ansible.cfg"
    lint_cfg = tmp_path / ".ansible-lint"
    log_file = tmp_path / "ansible-lint.log"

    # 2. Create ansible.cfg with log_path
    ansible_cfg.write_text(f"[defaults]\nlog_path={log_file}\n")

    # 3. Create invalid .ansible-lint
    lint_cfg.write_text("invalid_option: true\n")

    # 4. Run cli.get_config and verify console_stderr.print and _logger.error were called
    os.environ["ANSIBLE_CONFIG"] = str(ansible_cfg)
    original_handlers = list(logging.root.handlers)

    # Simulate Ansible's FileHandler setup when log_path is configured in a fresh process
    handler = logging.FileHandler(str(log_file))
    logging.root.addHandler(handler)

    try:
        with (
            patch("ansiblelint.cli.console_stderr.print") as mock_print,
            patch("ansiblelint.cli._logger.error") as mock_error,
            pytest.raises(SystemExit) as exc,
        ):
            cli.get_config(["-c", str(lint_cfg)])

        assert exc.value.code == 3

        # 5. Verify console_stderr.print was called with error message
        mock_print.assert_called()
        args, _ = mock_print.call_args
        assert "Invalid configuration file" in args[0]
        assert "invalid_option" in args[0]

        # 6. Verify _logger.error was also called because handlers are configured
        mock_error.assert_called_once()
        args, _ = mock_error.call_args
        assert "Invalid configuration file" in args[0]
    finally:
        os.environ.pop("ANSIBLE_CONFIG", None)
        handler.close()
        logging.root.handlers = original_handlers


def test_config_error_without_log_path(tmp_path: Path) -> None:
    """Verify that configuration errors are printed to stderr but NOT logged via _logger to avoid duplicates."""
    # 1. Setup temporary paths
    lint_cfg = tmp_path / ".ansible-lint"

    # 2. Create invalid .ansible-lint
    lint_cfg.write_text("invalid_option: true\n")

    original_handlers = list(logging.root.handlers)

    # 3. Run cli.get_config and verify only console_stderr.print is called
    try:
        with (
            patch("ansiblelint.cli.console_stderr.print") as mock_print,
            patch("ansiblelint.cli._logger.error") as mock_error,
            pytest.raises(SystemExit) as exc,
        ):
            cli.get_config(["-c", str(lint_cfg)])

        assert exc.value.code == 3

        # 4. Verify console_stderr.print was called
        mock_print.assert_called()
        args, _ = mock_print.call_args
        assert "Invalid configuration file" in args[0]
        assert "invalid_option" in args[0]

        # 5. Verify _logger.error was NOT called to avoid duplicate output to stderr
        mock_error.assert_not_called()
    finally:
        logging.root.handlers = original_handlers


def test_missing_config_error_with_log_path(tmp_path: Path) -> None:
    """Verify that missing configuration file errors are printed to stderr and logged even with log_path."""
    ansible_cfg = tmp_path / "ansible.cfg"
    log_file = tmp_path / "ansible-lint.log"
    missing_cfg = tmp_path / "non-existent.yml"

    ansible_cfg.write_text(f"[defaults]\nlog_path={log_file}\n")
    os.environ["ANSIBLE_CONFIG"] = str(ansible_cfg)
    original_handlers = list(logging.root.handlers)

    # Simulate Ansible's FileHandler setup when log_path is configured in a fresh process
    handler = logging.FileHandler(str(log_file))
    logging.root.addHandler(handler)

    try:
        with (
            patch("ansiblelint.cli.console_stderr.print") as mock_print,
            patch("ansiblelint.cli._logger.error") as mock_error,
            pytest.raises(SystemExit) as exc,
        ):
            cli.get_config(["-c", str(missing_cfg)])

        assert exc.value.code == 3

        mock_print.assert_called()
        args, _ = mock_print.call_args
        assert "Config file not found" in args[0]

        mock_error.assert_called_once()
        args, _ = mock_error.call_args
        assert "Config file not found" in args[0]
    finally:
        os.environ.pop("ANSIBLE_CONFIG", None)
        handler.close()
        logging.root.handlers = original_handlers


def test_missing_config_error_without_log_path(tmp_path: Path) -> None:
    """Verify that missing configuration file errors are printed but not logged via _logger when log_path is not set."""
    missing_cfg = tmp_path / "non-existent.yml"
    original_handlers = list(logging.root.handlers)

    try:
        with (
            patch("ansiblelint.cli.console_stderr.print") as mock_print,
            patch("ansiblelint.cli._logger.error") as mock_error,
            pytest.raises(SystemExit) as exc,
        ):
            cli.get_config(["-c", str(missing_cfg)])

        assert exc.value.code == 3

        mock_print.assert_called()
        args, _ = mock_print.call_args
        assert "Config file not found" in args[0]

        # Should not log via _logger to prevent duplicate output to stderr
        mock_error.assert_not_called()
    finally:
        logging.root.handlers = original_handlers
