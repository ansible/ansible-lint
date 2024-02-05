"""Test utils for ansible-lint."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ansiblelint.app import get_app

if TYPE_CHECKING:
    # https://github.com/PyCQA/pylint/issues/3240
    CompletedProcess = subprocess.CompletedProcess[Any]
    from ansiblelint.errors import MatchError
    from ansiblelint.rules import RulesCollection
else:
    CompletedProcess = subprocess.CompletedProcess

# pylint: disable=wrong-import-position
from ansiblelint.runner import Runner


class RunFromText:
    """Use Runner on temp files created from testing text snippets."""

    app = None

    def __init__(self, collection: RulesCollection) -> None:
        """Initialize a RunFromText instance with rules collection."""
        # Emulate command line execution initialization as without it Ansible module
        # would be loaded with incomplete module/role/collection list.
        if not self.app:  # pragma: no cover
            self.app = get_app(offline=True)

        self.collection = collection

    def _call_runner(self, path: Path) -> list[MatchError]:
        runner = Runner(path, rules=self.collection)
        return runner.run()

    def run(self, filename: Path) -> list[MatchError]:
        """Lints received filename."""
        return self._call_runner(filename)

    def run_playbook(
        self,
        playbook_text: str,
        prefix: str = "playbook",
    ) -> list[MatchError]:
        """Lints received text as a playbook."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", prefix=prefix) as fh:
            fh.write(playbook_text)
            fh.flush()
            results = self._call_runner(Path(fh.name))
        return results

    def run_role_tasks_main(
        self,
        tasks_main_text: str,
        tmp_path: Path,
    ) -> list[MatchError]:
        """Lints received text as tasks."""
        role_path = tmp_path
        tasks_path = role_path / "tasks"
        tasks_path.mkdir(parents=True, exist_ok=True)
        with (tasks_path / "main.yml").open("w", encoding="utf-8") as fh:
            fh.write(tasks_main_text)
            fh.flush()
        results = self._call_runner(role_path)
        shutil.rmtree(role_path)
        return results

    def run_role_meta_main(
        self,
        meta_main_text: str,
        temp_path: Path,
    ) -> list[MatchError]:
        """Lints received text as meta."""
        role_path = temp_path
        meta_path = role_path / "meta"
        meta_path.mkdir(parents=True, exist_ok=True)
        with (meta_path / "main.yml").open("w", encoding="utf-8") as fh:
            fh.write(meta_main_text)
            fh.flush()
        results = self._call_runner(role_path)
        shutil.rmtree(role_path)
        return results

    def run_role_defaults_main(
        self,
        defaults_main_text: str,
        tmp_path: Path,
    ) -> list[MatchError]:
        """Lints received text as vars file in defaults."""
        role_path = tmp_path
        defaults_path = role_path / "defaults"
        defaults_path.mkdir(parents=True, exist_ok=True)
        with (defaults_path / "main.yml").open("w", encoding="utf-8") as fh:
            fh.write(defaults_main_text)
            fh.flush()
        results = self._call_runner(role_path)
        shutil.rmtree(role_path)
        return results


def run_ansible_lint(
    *argv: str | Path,
    cwd: Path | None = None,
    executable: str | None = None,
    env: dict[str, str] | None = None,
    offline: bool = True,
) -> CompletedProcess:
    """Run ansible-lint on a given path and returns its output."""
    args = [str(item) for item in argv]
    if offline:  # pragma: no cover
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
        "COVERAGE_FILE",
        "COVERAGE_PROCESS_START",
        "HOME",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "NO_COLOR",
        "PATH",
        "PYTHONIOENCODING",
        "PYTHONPATH",
        "TERM",
        "VIRTUAL_ENV",
    ]

    _env = {} if env is None else env
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
        encoding="utf-8",
    )
