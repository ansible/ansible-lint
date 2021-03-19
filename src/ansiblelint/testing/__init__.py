"""Test utils for ansible-lint."""

import os
import shutil
import subprocess
import sys
import tempfile
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ansiblelint.prerun import prepare_environment

if TYPE_CHECKING:
    # https://github.com/PyCQA/pylint/issues/3240
    # pylint: disable=unsubscriptable-object
    CompletedProcess = subprocess.CompletedProcess[Any]
else:
    CompletedProcess = subprocess.CompletedProcess

# Emulate command line execution initialization as without it Ansible module
# would be loaded with incomplete module/role/collection list.
prepare_environment()

# pylint: disable=wrong-import-position
from ansiblelint.errors import MatchError  # noqa: E402
from ansiblelint.rules import RulesCollection  # noqa: E402
from ansiblelint.runner import Runner  # noqa: E402


class RunFromText:
    """Use Runner on temp files created from unittest text snippets."""

    def __init__(self, collection: RulesCollection) -> None:
        """Initialize a RunFromText instance with rules collection."""
        self.collection = collection

    def _call_runner(self, path: str) -> List["MatchError"]:
        runner = Runner(path, rules=self.collection)
        return runner.run()

    def run_playbook(self, playbook_text: str) -> List[MatchError]:
        """Lints received text as a playbook."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", prefix="playbook"
        ) as fp:
            fp.write(playbook_text)
            fp.flush()
            results = self._call_runner(fp.name)
        return results

    def run_role_tasks_main(self, tasks_main_text: str) -> List[MatchError]:
        """Lints received text as tasks."""
        role_path = tempfile.mkdtemp(prefix='role_')
        tasks_path = os.path.join(role_path, 'tasks')
        os.makedirs(tasks_path)
        with open(os.path.join(tasks_path, 'main.yml'), 'w') as fp:
            fp.write(tasks_main_text)
        results = self._call_runner(role_path)
        shutil.rmtree(role_path)
        return results

    def run_role_meta_main(self, meta_main_text: str) -> List[MatchError]:
        """Lints received text as meta."""
        role_path = tempfile.mkdtemp(prefix='role_')
        meta_path = os.path.join(role_path, 'meta')
        os.makedirs(meta_path)
        with open(os.path.join(meta_path, 'main.yml'), 'w') as fp:
            fp.write(meta_main_text)
        results = self._call_runner(role_path)
        shutil.rmtree(role_path)
        return results


def run_ansible_lint(
    *argv: str,
    cwd: Optional[str] = None,
    executable: Optional[str] = None,
    env: Optional[Dict[str, str]] = None
) -> CompletedProcess:
    """Run ansible-lint on a given path and returns its output."""
    if not executable:
        executable = sys.executable
        args = [sys.executable, "-m", "ansiblelint", *argv]
    else:
        args = [executable, *argv]

    # It is not safe to pass entire env for testing as other tests would
    # pollute the env, causing weird behaviors, so we pass only a safe list of
    # vars.
    safe_list = [
        'LANG',
        'LC_ALL',
        'LC_CTYPE',
        'NO_COLOR',
        'PATH',
        'PYTHONIOENCODING',
        'PYTHONPATH',
        'TERM',
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
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,  # needed when command is a list
        check=False,
        cwd=cwd,
        env=_env,
        universal_newlines=True,
    )
