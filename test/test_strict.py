"""Test strict mode."""
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
    if strict:
        args.insert(0, "--strict")
    result = run_ansible_lint(*args)
    assert result.returncode == returncode
    assert "key-order[task]" in result.stdout
    summary_line = result.stderr.splitlines()[-1]
    assert message in summary_line
