"""Tests related to prerun part of the linter."""
import os

from flaky import flaky

from ansiblelint.testing import run_ansible_lint


# https://github.com/box/flaky/issues/170
@flaky(max_runs=3)  # type: ignore
def test_prerun_reqs_v1() -> None:
    """Checks that the linter can auto-install requirements v1 when found."""
    cwd = os.path.realpath(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "..", "examples", "reqs_v1"
        )
    )
    result = run_ansible_lint("-v", ".", cwd=cwd)
    assert "Running ansible-galaxy role install" in result.stderr, result.stderr
    assert (
        "Running ansible-galaxy collection install" not in result.stderr
    ), result.stderr
    assert result.returncode == 0, result


@flaky(max_runs=3)  # type: ignore
def test_prerun_reqs_v2() -> None:
    """Checks that the linter can auto-install requirements v2 when found."""
    cwd = os.path.realpath(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "..", "examples", "reqs_v2"
        )
    )
    result = run_ansible_lint("-v", ".", cwd=cwd)
    assert "Running ansible-galaxy role install" in result.stderr, result.stderr
    assert "Running ansible-galaxy collection install" in result.stderr, result.stderr
    assert result.returncode == 0, result
