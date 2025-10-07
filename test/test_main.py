"""Tests related to ansiblelint.__main__ module."""

import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Mapping
from http.client import RemoteDisconnected
from os.path import abspath
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from ansiblelint.config import get_version_warning, options
from ansiblelint.constants import RC
from ansiblelint.loaders import yaml_load_safe


@pytest.mark.parametrize(
    ("in_path"),
    (False, True),
    ids=("in", "missing"),
)
def test_call_from_outside_venv(in_path: bool) -> None:
    """Asserts ability to be called w/ or w/o venv activation."""
    git_location = shutil.which("git")
    if not git_location:
        pytest.fail("git not found")
    git_path = Path(git_location).parent
    py_path = Path(sys.executable).parent.resolve().as_posix()

    env = os.environ.copy()
    env["VIRTUAL_ENV"] = ""
    env["NO_COLOR"] = "1"
    if in_path:
        # VIRTUAL_ENV obliterated here to emulate call from outside a virtual environment
        env["HOME"] = Path.home().as_posix()
        env["PATH"] = git_path.as_posix()
    else:
        if py_path not in env["PATH"]:
            env["PATH"] = f"{py_path}:{env['PATH']}"

    for v in ("COVERAGE_FILE", "COVERAGE_PROCESS_START"):
        if v in os.environ:
            env[v] = os.environ[v]

    # Passing custom env prevents the process from inheriting PATH or other
    # environment variables from the current process, so we emulate being
    # called from outside the venv.
    proc = subprocess.run(
        [f"{py_path}/ansible-lint", "--version"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0, proc
    warning_found = "PATH altered to include" in proc.stderr
    assert warning_found is in_path


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
    assert get_version_warning() == ""  # noqa: PLC1901


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
        assert get_version_warning() == ""  # noqa: PLC1901


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
    # 2.19 had different errors
    assert any(
        x in proc.stderr
        for x in (
            "Invalid type for configuration option setting: CACHE_PLUGIN_TIMEOUT",
            "has an invalid value: Invalid type provided for 'int': 'invalid-value'",
            "has an invalid value: Invalid value provided for 'integer': 'invalid-value'",
        )
    ), proc.stderr


def test_list_tags() -> None:
    """Asserts that we can list tags and that the output is parseable yaml."""
    result = subprocess.run(
        ["ansible-lint", "--list-tags"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = yaml_load_safe(result.stdout)
    assert isinstance(data, Mapping)
    for key, value in data.items():
        assert isinstance(key, str)
        assert isinstance(value, list)
        for item in value:
            assert isinstance(item, str)


def test_ro_venv() -> None:
    """Tests behavior when the virtual environment is read-only."""
    tox_work_dir = os.environ.get("TOX_WORK_DIR", ".tox")
    venv_path = f"{tox_work_dir}/ro"
    prerelease_flag = "" if sys.version_info < (3, 14) else "--pre "
    commands = [
        f"mkdir -p {venv_path}",
        f"chmod -R a+w {venv_path}",
        f"rm -rf {venv_path}",
        f"python -m venv --symlinks {venv_path}",
        f"{venv_path}/bin/python -m pip install {prerelease_flag}-q -e .",
        f"chmod -R a-w {venv_path}",
        # running with a ro venv and default cwd
        f"{venv_path}/bin/ansible-lint --version",
        # running from a read-only cwd:
        f"cd / && {abspath(venv_path)}/bin/ansible-lint --version",  # noqa: PTH100
        # running with a ro venv and a custom project path in forced non-online mode, so it will need to install requirements
        f"{venv_path}/bin/ansible-lint -vv --no-offline --project-dir ./examples/reqs_v2/ ./examples/reqs_v2/",
    ]
    for cmd in commands:
        result = subprocess.run(
            cmd, capture_output=True, shell=True, text=True, check=False
        )
        assert result.returncode == 0, (
            f"Got {result.returncode} running {cmd}\n\tstderr: {result.stderr}\n\tstdout: {result.stdout}"
        )
