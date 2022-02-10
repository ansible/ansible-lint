"""Tests related to prerun part of the linter."""
import os
import re
import subprocess
import sys
from typing import Callable, List

import pytest
from _pytest.monkeypatch import MonkeyPatch
from flaky import flaky

from ansiblelint import prerun
from ansiblelint.constants import INVALID_PREREQUISITES_RC
from ansiblelint.testing import run_ansible_lint

EXECDIR = os.path.dirname(sys.executable)

Deactivator = Callable[[bool], str]
DeactivateVenv = Callable[[], Deactivator]


@pytest.fixture
def deactivate_venv(monkeypatch: MonkeyPatch) -> Deactivator:
    """Deliver a function to deactivate the current venv, if any, if requested, by removing it's bin dir from $PATH."""

    def deactiveator(deactivate: bool) -> str:
        if deactivate:
            search_path = os.get_exec_path()
            try:
                pos = search_path.index(EXECDIR)
            except ValueError:
                return ""
            del search_path[pos]
            monkeypatch.setenv("PATH", ";".join(search_path))
            return EXECDIR
        return ""

    return deactiveator


# https://github.com/box/flaky/issues/170
@flaky(max_runs=3)  # type: ignore
@pytest.mark.parametrize(
    ("deactivate"),
    (
        (False),
        (True),
    ),
    ids=("venv activated", "venv deactivated"),
)
def test_prerun_reqs_v1(deactivate: bool, deactivate_venv: Deactivator) -> None:
    """Checks that the linter can auto-install requirements v1 when found."""
    cwd = os.path.realpath(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "..", "examples", "reqs_v1"
        )
    )
    execdir = deactivate_venv(deactivate)
    result = run_ansible_lint("-v", ".", cwd=cwd)

    ansible_galaxy = os.path.join(execdir, "ansible-galaxy")
    assert f"Running {ansible_galaxy} role install" in result.stderr, result.stderr
    assert (
        f"Running {ansible_galaxy} collection install" not in result.stderr
    ), result.stderr
    assert result.returncode == 0, result


@flaky(max_runs=3)  # type: ignore
@pytest.mark.parametrize(
    ("executable"),  # Run with `python -m` or the venv command: issue #1507
    (
        (None),
        (os.path.join(os.path.dirname(sys.executable), "ansible-lint")),
    ),
    ids=(
        "run as ansiblelint python module",
        "run via path to the virtualenv's ansible-lint command",
    ),
)
@pytest.mark.parametrize(
    ("deactivate"),
    (
        (False),
        (True),
    ),
    ids=("venv activated", "venv deactivated"),
)
def test_prerun_reqs_v2(
    executable: str, deactivate: bool, deactivate_venv: Deactivator
) -> None:
    """Checks that the linter can auto-install requirements v2 when found."""
    cwd = os.path.realpath(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "..", "examples", "reqs_v2"
        )
    )
    execdir = deactivate_venv(deactivate)
    result = run_ansible_lint("-v", ".", cwd=cwd, executable=executable)

    # These first 2 assertations are written to pass both with the test
    # as-it-is before the fix of issue #1507 and after the fix.
    # (See: https://github.com/ansible-community/ansible-lint/issues/1507)
    # But these assertations are written as much like the "before" version
    # of this test as possible, to demonstrate that the assertion
    # itself is not substantively changed by the fix.
    # When these asserations fail, without the #1507 patch,
    # it demonstrates that ansible-lint does not run in a virtual environment
    # unless that environment is activated.
    assert re.search(
        "Running [^ ]*ansible-galaxy role install", result.stderr
    ), result.stderr
    assert re.search(
        "Running [^ ]*ansible-galaxy collection install", result.stderr
    ), result.stderr

    # Commands are given with or without paths, as expected.
    ansible_galaxy = os.path.join(execdir, "ansible-galaxy")
    assert f"Running {ansible_galaxy} role install" in result.stderr, result.stderr
    assert (
        f"Running {ansible_galaxy} collection install" in result.stderr
    ), result.stderr
    assert result.returncode == 0, result


def test__update_env_no_old_value_no_default_no_value(monkeypatch: MonkeyPatch) -> None:
    """Make sure empty value does not touch environment."""
    monkeypatch.delenv("DUMMY_VAR", raising=False)

    prerun._update_env("DUMMY_VAR", [])

    assert "DUMMY_VAR" not in os.environ


def test__update_env_no_old_value_no_value(monkeypatch: MonkeyPatch) -> None:
    """Make sure empty value does not touch environment."""
    monkeypatch.delenv("DUMMY_VAR", raising=False)

    prerun._update_env("DUMMY_VAR", [], "a:b")

    assert "DUMMY_VAR" not in os.environ


def test__update_env_no_default_no_value(monkeypatch: MonkeyPatch) -> None:
    """Make sure empty value does not touch environment."""
    monkeypatch.setenv("DUMMY_VAR", "a:b")

    prerun._update_env("DUMMY_VAR", [])

    assert os.environ["DUMMY_VAR"] == "a:b"


@pytest.mark.parametrize(
    ("value", "result"),
    (
        (["a"], "a"),
        (["a", "b"], "a:b"),
        (["a", "b", "c"], "a:b:c"),
    ),
)
def test__update_env_no_old_value_no_default(
    monkeypatch: MonkeyPatch, value: List[str], result: str
) -> None:
    """Values are concatenated using : as the separator."""
    monkeypatch.delenv("DUMMY_VAR", raising=False)

    prerun._update_env("DUMMY_VAR", value)

    assert os.environ["DUMMY_VAR"] == result


@pytest.mark.parametrize(
    ("default", "value", "result"),
    (
        ("a:b", ["c"], "a:b:c"),
        ("a:b", ["c:d"], "a:b:c:d"),
    ),
)
def test__update_env_no_old_value(
    monkeypatch: MonkeyPatch, default: str, value: List[str], result: str
) -> None:
    """Values are appended to default value."""
    monkeypatch.delenv("DUMMY_VAR", raising=False)

    prerun._update_env("DUMMY_VAR", value, default)

    assert os.environ["DUMMY_VAR"] == result


@pytest.mark.parametrize(
    ("old_value", "value", "result"),
    (
        ("a:b", ["c"], "a:b:c"),
        ("a:b", ["c:d"], "a:b:c:d"),
    ),
)
def test__update_env_no_default(
    monkeypatch: MonkeyPatch, old_value: str, value: List[str], result: str
) -> None:
    """Values are appended to preexisting value."""
    monkeypatch.setenv("DUMMY_VAR", old_value)

    prerun._update_env("DUMMY_VAR", value)

    assert os.environ["DUMMY_VAR"] == result


@pytest.mark.parametrize(
    ("old_value", "default", "value", "result"),
    (
        ("", "", ["e"], "e"),
        ("a", "", ["e"], "a:e"),
        ("", "c", ["e"], "e"),
        ("a", "c", ["e:f"], "a:e:f"),
    ),
)
def test__update_env(
    monkeypatch: MonkeyPatch,
    old_value: str,
    default: str,
    value: List[str],
    result: str,
) -> None:
    """Defaults are ignored when preexisting value is present."""
    monkeypatch.setenv("DUMMY_VAR", old_value)

    prerun._update_env("DUMMY_VAR", value)

    assert os.environ["DUMMY_VAR"] == result


def test_require_collection_wrong_version() -> None:
    """Tests behaviour of require_collection."""
    subprocess.check_output(
        [
            "ansible-galaxy",
            "collection",
            "install",
            "containers.podman",
            "-p",
            "~/.ansible/collections",
        ]
    )
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        prerun.require_collection("containers.podman", "9999.9.9")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == INVALID_PREREQUISITES_RC


@pytest.mark.parametrize(
    ("name", "version"),
    (
        ("fake_namespace.fake_name", None),
        ("fake_namespace.fake_name", "9999.9.9"),
    ),
)
def test_require_collection_missing(name: str, version: str) -> None:
    """Tests behaviour of require_collection, missing case."""
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        prerun.require_collection(name, version)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == INVALID_PREREQUISITES_RC


def test_ansible_config_get() -> None:
    """Check test_ansible_config_get."""
    paths = prerun.ansible_config_get("COLLECTIONS_PATHS", list)
    assert isinstance(paths, list)
    assert len(paths) > 0


def test_install_collection() -> None:
    """Check that valid collection installs do not fail."""
    prerun.install_collection("containers.podman:>=1.0")


def test_install_collection_fail() -> None:
    """Check that invalid collection install fails."""
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        prerun.install_collection("containers.podman:>=9999.0")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == INVALID_PREREQUISITES_RC
