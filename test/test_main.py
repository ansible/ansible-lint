"""Tests related to ansiblelint.__main__ module."""

import os
import shutil
import subprocess
import sys
import tempfile
import time
from http.client import RemoteDisconnected
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from ansiblelint.config import get_version_warning, options
from ansiblelint.constants import RC


@pytest.mark.parametrize(
    ("expected_warning"),
    (False, True),
    ids=("normal", "isolated"),
)
def test_call_from_outside_venv(expected_warning: bool) -> None:
    """Asserts ability to be called w/ or w/o venv activation."""
    git_location = shutil.which("git")
    if not git_location:
        pytest.fail("git not found")
    git_path = Path(git_location).parent

    if expected_warning:
        env = {"HOME": str(Path.home()), "PATH": str(git_path)}
    else:
        env = os.environ.copy()

    for v in ("COVERAGE_FILE", "COVERAGE_PROCESS_START"):
        if v in os.environ:
            env[v] = os.environ[v]

    py_path = Path(sys.executable).parent
    # Passing custom env prevents the process from inheriting PATH or other
    # environment variables from the current process, so we emulate being
    # called from outside the venv.
    proc = subprocess.run(
        [str(py_path / "ansible-lint"), "--version"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0, proc
    warning_found = "PATH altered to include" in proc.stderr
    assert warning_found is expected_warning


@pytest.mark.parametrize(
    ("ver_diff", "found", "check", "outlen"),
    (
        pytest.param("v1.2.2", True, "pre-release", 1, id="0"),
        pytest.param("v1.2.3", False, "", 1, id="1"),
        pytest.param("v1.2.4", True, "new release", 2, id="2"),
    ),
)
def test_get_version_warning(
    mocker: MockerFixture,
    ver_diff: str,
    found: bool,
    check: str,
    outlen: int,
) -> None:
    """Assert get_version_warning working as expected."""
    data = f'{{"html_url": "https://127.0.0.1", "tag_name": "{ver_diff}"}}'
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


def test_get_version_warning_no_pip(mocker: MockerFixture) -> None:
    """Test that we do not display any message if install method is not pip."""
    mocker.patch("ansiblelint.config.guess_install_method", return_value="")
    assert get_version_warning() == ""


def test_get_version_warning_remote_disconnect(mocker: MockerFixture) -> None:
    """Test that we can handle remote disconnect when fetching release url."""
    mocker.patch("urllib.request.urlopen", side_effect=RemoteDisconnected)
    try:
        get_version_warning()
    except RemoteDisconnected:
        pytest.fail("Failed to handle a remote disconnect")


def test_get_version_warning_offline(mocker: MockerFixture) -> None:
    """Test that offline mode does not display any message."""
    with tempfile.TemporaryDirectory() as temporary_directory:
        # ensures a real cache_file is not loaded
        mocker.patch("ansiblelint.config.CACHE_DIR", Path(temporary_directory))
        options.offline = True
        assert get_version_warning() == ""


@pytest.mark.parametrize(
    ("lintable"),
    (
        pytest.param("examples/playbooks/nodeps.yml", id="1"),
        pytest.param("examples/playbooks/nodeps2.yml", id="2"),
    ),
)
def test_nodeps(lintable: str) -> None:
    """Asserts ability to be called w/ or w/o venv activation."""
    env = os.environ.copy()
    env["ANSIBLE_LINT_NODEPS"] = "1"
    py_path = Path(sys.executable).parent
    proc = subprocess.run(
        [str(py_path / "ansible-lint"), lintable],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0, proc


def test_broken_ansible_cfg() -> None:
    """Asserts behavior when encountering broken ansible.cfg files."""
    py_path = Path(sys.executable).parent
    proc = subprocess.run(
        [str(py_path / "ansible-lint"), "--version"],
        check=False,
        capture_output=True,
        text=True,
        cwd="test/fixtures/broken-ansible.cfg",
    )
    assert proc.returncode == RC.INVALID_CONFIG, proc
    assert (
        "Invalid type for configuration option setting: CACHE_PLUGIN_TIMEOUT"
        in proc.stderr
    )
