"""Test utils for ansible-lint."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from typing import TYPE_CHECKING, Any

from ansiblelint.app import get_app
from ansiblelint.rules import RulesCollection

if TYPE_CHECKING:
    # https://github.com/PyCQA/pylint/issues/3240
    # pylint: disable=unsubscriptable-object
    CompletedProcess = subprocess.CompletedProcess[Any]
    from ansiblelint.errors import MatchError  # noqa: E402
else:
    CompletedProcess = subprocess.CompletedProcess

# pylint: disable=wrong-import-position
from ansiblelint.runner import Runner  # noqa: E402


class RunFromText:
    """Use Runner on temp files created from testing text snippets."""

    app = None

    def __init__(self, collection: RulesCollection) -> None:
        """Initialize a RunFromText instance with rules collection."""
        # Emulate command line execution initialization as without it Ansible module
        # would be loaded with incomplete module/role/collection list.
        if not self.app:
            self.app = get_app()

        self.collection = collection

    def _call_runner(self, path: str) -> list[MatchError]:
        runner = Runner(path, rules=self.collection)
        return runner.run()

    def run(self, filename: str) -> list[MatchError]:
        """Lints received filename."""
        return self._call_runner(filename)

    def run_playbook(self, playbook_text: str) -> list[MatchError]:
        """Lints received text as a playbook."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", prefix="playbook"
        ) as fh:
            fh.write(playbook_text)
            fh.flush()
            results = self._call_runner(fh.name)
        return results

    def run_role_tasks_main(self, tasks_main_text: str) -> list[MatchError]:
        """Lints received text as tasks."""
        role_path = tempfile.mkdtemp(prefix="role_")
        tasks_path = os.path.join(role_path, "tasks")
        os.makedirs(tasks_path)
        with open(os.path.join(tasks_path, "main.yml"), "w", encoding="utf-8") as fh:
            fh.write(tasks_main_text)
            fh.flush()
        results = self._call_runner(role_path)
        shutil.rmtree(role_path)
        return results

    def run_role_meta_main(self, meta_main_text: str) -> list[MatchError]:
        """Lints received text as meta."""
        role_path = tempfile.mkdtemp(prefix="role_")
        meta_path = os.path.join(role_path, "meta")
        os.makedirs(meta_path)
        with open(os.path.join(meta_path, "main.yml"), "w", encoding="utf-8") as fh:
            fh.write(meta_main_text)
            fh.flush()
        results = self._call_runner(role_path)
        shutil.rmtree(role_path)
        return results

    def run_role_defaults_main(self, defaults_main_text: str) -> list[MatchError]:
        """Lints received text as vars file in defaults."""
        role_path = tempfile.mkdtemp(prefix="role_")
        defaults_path = os.path.join(role_path, "defaults")
        os.makedirs(defaults_path)
        with open(os.path.join(defaults_path, "main.yml"), "w", encoding="utf-8") as fh:
            fh.write(defaults_main_text)
            fh.flush()
        results = self._call_runner(role_path)
        shutil.rmtree(role_path)
        return results


def run_ansible_lint(
    *argv: str,
    cwd: str | None = None,
    executable: str | None = None,
    env: dict[str, str] | None = None,
    offline: bool = True,
) -> CompletedProcess:
    """Run ansible-lint on a given path and returns its output."""
    args = [*argv]
    if offline:
        args.insert(0, "--offline")

    if not executable:
        executable = sys.executable
        args = [sys.executable, "-m", "ansiblelint", *args]
    else:
        args = [executable, *args]

    # It is not safe to pass entire env for testing as other tests would
    # pollute the env, causing weird behaviors, so we pass only a safe list of
    # vars.
    safe_list = [
        "HOME",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "NO_COLOR",
        "PATH",
        "PYTHONIOENCODING",
        "PYTHONPATH",
        "TERM",
    ]

    if env is None:
        _env = {}
    else:
        _env = env
    for v in safe_list:
        if v in os.environ and v not in _env:
            _env[v] = os.environ[v]

    return subprocess.run(
        args,
        capture_output=True,
        shell=False,  # needed when command is a list
        check=False,
        cwd=cwd,
        env=_env,
        text=True,
    )
