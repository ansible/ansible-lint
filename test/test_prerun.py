"""Tests related to prerun part of the linter."""
import os

from ansiblelint.testing import run_ansible_lint


def test_prerun_reqs_v1() -> None:
    """Checks that the linter can auto-install requirements v1 when found."""
    cwd = os.path.realpath(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "..", "examples", "reqs_v1"
        )
    )
    result = run_ansible_lint(".", cwd=cwd)
    assert "Running ansible-galaxy role install" in result.stderr
    assert "Running ansible-galaxy collection install" not in result.stderr
    assert result.returncode == 0


def test_prerun_reqs_v2() -> None:
    """Checks that the linter can auto-install requirements v2 when found."""
    cwd = os.path.realpath(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "..", "examples", "reqs_v2"
        )
    )
    result = run_ansible_lint(".", cwd=cwd)
    assert "Running ansible-galaxy role install" in result.stderr
    assert "Running ansible-galaxy collection install" in result.stderr
    assert result.returncode == 0
