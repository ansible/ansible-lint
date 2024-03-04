"""Test strict mode."""

import os

import pytest

from ansiblelint.testing import run_ansible_lint


@pytest.mark.parametrize(
    ("strict", "returncode", "message"),
    (
        pytest.param(True, 2, "Failed", id="on"),
        pytest.param(False, 0, "Passed", id="off"),
    ),
)
def test_strict(strict: bool, returncode: int, message: str) -> None:
    """Test running from inside meta folder."""
    args = ["examples/playbooks/strict-mode.yml"]
    env = os.environ.copy()
    env["NO_COLOR"] = "1"
    if strict:
        args.insert(0, "--strict")
    result = run_ansible_lint(*args, env=env)
    assert result.returncode == returncode
    assert "args[module]" in result.stdout
    for summary_line in result.stderr.splitlines():
        if summary_line.startswith(message):
            break
    else:
        pytest.fail(f"Failed to find {message} inside stderr output")
