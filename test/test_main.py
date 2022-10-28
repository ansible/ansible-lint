"""Tests related to ansiblelint.__main__ module."""
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

from ansiblelint.config import get_version_warning


@pytest.mark.parametrize(
    ("expected_warning"),
    (False, True),
    ids=("normal", "isolated"),
)
def test_call_from_outside_venv(expected_warning: bool) -> None:
    """Asserts ability to be called w/ or w/o venv activation."""
    env = None
    if expected_warning:
        env = {"HOME": Path.home()}
    py_path = os.path.dirname(sys.executable)
    # Passing custom env prevents the process from inheriting PATH or other
    # environment variables from the current process, so we emulate being
    # called from outside the venv.
    proc = subprocess.run(
        [f"{py_path}/ansible-lint", "--version"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    warning_found = "PATH altered to include" in proc.stderr
    assert warning_found is expected_warning


@pytest.mark.parametrize(
    ("ver_diff", "found", "check", "outlen"),
    (
        ("v1.2.2", True, "pre-release", 1),
        ("v1.2.3", False, "", 1),
        ("v1.2.4", True, "new release", 2),
    ),
)
def test_get_version_warning(
    mocker: Any, ver_diff: str, found: bool, check: str, outlen: int
) -> None:
    """Assert get_version_warning working as expected."""
    data = '{"html_url": "https://127.0.0.1", "tag_name": "' + f"{ver_diff}" + '"}'
    # simulate cache file
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.path.getmtime", return_value=time.time())
    mocker.patch("builtins.open", mocker.mock_open(read_data=data))
    # overwrite ansible-lint version
    mocker.patch("ansiblelint.config.__version__", "1.2.3")
    # overwrite install method to custom one. This one will increase msg line count
    # to easily detect unwanted call to it.
    mocker.patch("ansiblelint.config.guess_install_method", return_value="\n")
    msg = get_version_warning()

    if not found:
        assert msg == check
    else:
        assert check in msg
    assert len(msg.split("\n")) == outlen
