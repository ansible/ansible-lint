"""Tests related to ansiblelint.__main__ module."""
import os
import subprocess
import sys
from pathlib import Path

import pytest


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
