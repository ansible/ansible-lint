"""Tests related to role paths."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ansiblelint.constants import RC
from ansiblelint.testing import run_ansible_lint
from ansiblelint.text import strip_ansi_escape


@pytest.fixture(name="local_test_dir")
def fixture_local_test_dir() -> Path:
    """Fixture to return local test directory."""
    return Path(__file__).resolve().parent.parent / "examples"


def test_run_single_role_path_no_trailing_slash_module(local_test_dir: Path) -> None:
    """Test that a role path without a trailing slash is accepted."""
    cwd = local_test_dir
    role_path = "roles/test-role"

    result = run_ansible_lint(role_path, cwd=cwd)
    assert "Use shell only when shell functionality is required" in result.stdout


def test_run_single_role_path_no_trailing_slash_script(local_test_dir: Path) -> None:
    """Test that a role path without a trailing slash is accepted."""
    cwd = local_test_dir
    role_path = "roles/test-role"

    result = run_ansible_lint(role_path, cwd=cwd, executable="ansible-lint")
    assert "Use shell only when shell functionality is required" in result.stdout


def test_run_single_role_path_with_trailing_slash(local_test_dir: Path) -> None:
    """Test that a role path with a trailing slash is accepted."""
    cwd = local_test_dir
    role_path = "roles/test-role/"

    result = run_ansible_lint(role_path, cwd=cwd)
    assert "Use shell only when shell functionality is required" in result.stdout


def test_run_multiple_role_path_no_trailing_slash(local_test_dir: Path) -> None:
    """Test that multiple roles paths without a trailing slash are accepted."""
    cwd = local_test_dir
    role_path = "roles/test-role"

    result = run_ansible_lint(role_path, cwd=cwd)
    assert "Use shell only when shell functionality is required" in result.stdout


def test_run_multiple_role_path_with_trailing_slash(local_test_dir: Path) -> None:
    """Test that multiple roles paths without a trailing slash are accepted."""
    cwd = local_test_dir
    role_path = "roles/test-role/"

    result = run_ansible_lint(role_path, cwd=cwd)
    assert "Use shell only when shell functionality is required" in result.stdout


def test_run_inside_role_dir(local_test_dir: Path) -> None:
    """Tests execution from inside a role."""
    cwd = local_test_dir / "roles" / "test-role"
    role_path = "."

    result = run_ansible_lint(role_path, cwd=cwd)
    assert "Use shell only when shell functionality is required" in result.stdout


def test_run_role_three_dir_deep(local_test_dir: Path) -> None:
    """Tests execution from deep inside a role."""
    cwd = local_test_dir
    role_path = "testproject/roles/test-role"

    result = run_ansible_lint(role_path, cwd=cwd)
    assert "Use shell only when shell functionality is required" in result.stdout


def test_run_playbook(local_test_dir: Path) -> None:
    """Call ansible-lint the way molecule does."""
    cwd = local_test_dir / "roles" / "test-role"
    lintable = "molecule/default/include-import-role.yml"
    role_path = str(Path(cwd).parent.resolve())

    env = os.environ.copy()
    env["ANSIBLE_ROLES_PATH"] = role_path
    env["NO_COLOR"] = "1"

    result = run_ansible_lint("-f", "pep8", lintable, cwd=cwd, env=env)
    # All 4 failures are expected to be found inside the included role and not
    # from the playbook given as argument.
    assert result.returncode == RC.VIOLATIONS_FOUND
    assert "tasks/main.yml:2: command-instead-of-shell" in result.stdout
    assert "tasks/world.yml:2: name[missing]" in result.stdout


@pytest.mark.parametrize(
    ("args", "expected_msg"),
    (
        pytest.param(
            [],
            "role-name: Role name invalid-name does not match",
            id="normal",
        ),
        pytest.param(["--skip-list", "role-name"], "", id="skipped"),
    ),
)
def test_run_role_name_invalid(
    local_test_dir: Path,
    args: list[str],
    expected_msg: str,
) -> None:
    """Test run with a role with invalid name."""
    cwd = local_test_dir
    role_path = "roles/invalid-name"

    result = run_ansible_lint(*args, role_path, cwd=cwd)
    assert result.returncode == (2 if expected_msg else 0), result
    if expected_msg:
        assert expected_msg in strip_ansi_escape(result.stdout)


def test_run_role_name_with_prefix(local_test_dir: Path) -> None:
    """Test run where role path has a prefix."""
    cwd = local_test_dir
    role_path = "roles/ansible-role-foo"

    result = run_ansible_lint("-v", role_path, cwd=cwd)
    assert len(result.stdout) == 0
    assert result.returncode == 0


def test_run_role_name_from_meta(local_test_dir: Path) -> None:
    """Test running from inside meta folder."""
    cwd = local_test_dir
    role_path = "roles/valid-due-to-meta"

    result = run_ansible_lint("-v", role_path, cwd=cwd)
    assert len(result.stdout) == 0
    assert result.returncode == 0


def test_run_invalid_role_name_from_meta(local_test_dir: Path) -> None:
    """Test invalid role from inside meta folder."""
    cwd = local_test_dir
    role_path = "roles/invalid_due_to_meta"

    result = run_ansible_lint(role_path, cwd=cwd)
    assert (
        "role-name: Role name invalid-due-to-meta does not match"
        in strip_ansi_escape(result.stdout)
    )


def test_run_single_role_path_with_roles_path_env(local_test_dir: Path) -> None:
    """Test for role name collision with ANSIBLE_ROLES_PATH.

    Test if ansible-lint chooses the role in the current directory when the role
    specified as parameter exists in the current directory and the ANSIBLE_ROLES_PATH.
    """
    cwd = local_test_dir
    role_path = "roles/test-role"

    env = os.environ.copy()
    env["ANSIBLE_ROLES_PATH"] = os.path.realpath((cwd / "../examples/roles").resolve())

    result = run_ansible_lint(role_path, cwd=cwd, env=env)
    assert "Use shell only when shell functionality is required" in result.stdout


@pytest.mark.parametrize(
    ("result", "env"),
    (
        (True, {"GITHUB_ACTIONS": "true", "GITHUB_WORKFLOW": "foo", "NO_COLOR": "1"}),
        (False, None),
    ),
    ids=("on", "off"),
)
def test_run_playbook_github(result: bool, env: dict[str, str]) -> None:
    """Call ansible-lint simulating GitHub Actions environment."""
    cwd = Path(__file__).parent.parent.resolve()
    role_path = "examples/playbooks/example.yml"

    if env is None:
        env = {}
    env["PATH"] = os.environ["PATH"]
    result_gh = run_ansible_lint(role_path, cwd=cwd, env=env)

    expected = (
        "::error file=examples/playbooks/example.yml,line=44,severity=VERY_LOW,title=package-latest::"
        "Package installs should not use latest"
    )
    assert (expected in result_gh.stderr) is result


def test_run_role_identified(local_test_dir: Path) -> None:
    """Test that role name is identified correctly."""
    cwd = local_test_dir

    env = os.environ.copy()
    env["ANSIBLE_ROLES_PATH"] = os.path.realpath(
        (cwd / "../examples/roles/role_detection").resolve(),
    )
    result = run_ansible_lint(
        Path("roles/role_detection/foo/defaults/main.yml"),
        cwd=cwd,
        env=env,
    )
    assert result.returncode == RC.SUCCESS


def test_run_role_identified_prefix_missing(local_test_dir: Path) -> None:
    """Test that role name is identified correctly, with prefix violations."""
    cwd = local_test_dir

    env = os.environ.copy()
    env["ANSIBLE_ROLES_PATH"] = os.path.realpath(
        (cwd / "../examples/roles/role_detection/base").resolve(),
    )
    result = run_ansible_lint(
        Path("roles/role_detection/base/bar/defaults/main.yml"),
        cwd=cwd,
        env=env,
    )
    assert result.returncode == RC.VIOLATIONS_FOUND
    assert (
        "Variables names from within roles should use bar_ as a prefix" in result.stdout
    )
    assert (
        "Variables names from within roles should use bar_ as a prefix" in result.stdout
    )
