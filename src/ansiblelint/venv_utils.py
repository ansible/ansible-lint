"""Utilities supporting virtual environments."""

# We run various ansible command line tools (and detect the ansible version
# by executing `ansible --version`).
# The executable we want to run may not be in $PATH, especially if we
# are running in a virtual environment that's not been activated.

import os
import pathlib
import subprocess
import sys
from functools import lru_cache
from typing import TYPE_CHECKING, Any, List

if TYPE_CHECKING:
    # https://github.com/PyCQA/pylint/issues/3240
    # pylint: disable=unsubscriptable-object
    CompletedProcess = subprocess.CompletedProcess[Any]
else:
    CompletedProcess = subprocess.CompletedProcess


def _normalize(path: str) -> pathlib.Path:
    # pathlib.Path takes care of MS Windows case-insensitivity
    return pathlib.Path(os.path.realpath(os.path.normpath(os.path.expanduser(path))))


def _get_search_path() -> List[pathlib.Path]:
    return [_normalize(path) for path in os.get_exec_path()]


@lru_cache()
def _get_venv_path() -> str:
    venv_dir = _normalize(os.path.dirname(sys.executable))
    search_path = _get_search_path()
    if venv_dir in search_path or search_path and search_path[0] == pathlib.Path("."):
        return ""
    return str(venv_dir)


def add_venv_path(cmd: str) -> str:
    """Prepend the path to the venv, if any, to the supplied command."""
    return os.path.join(_get_venv_path(), cmd)


def run_ansible_version() -> CompletedProcess:
    """Run `ansible --version` and return the result."""
    return subprocess.run(
        args=[add_venv_path("ansible"), "--version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=False,
    )
