"""Test utils for ansible-lint."""

import os
import shutil
import subprocess
import sys
import tempfile
from typing import TYPE_CHECKING, Dict, List

from ansible import __version__ as ansible_version_str

from ansiblelint.runner import Runner

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError


ANSIBLE_MAJOR_VERSION = tuple(map(int, ansible_version_str.split('.')[:2]))


class RunFromText(object):
    """Use Runner on temp files created from unittest text snippets."""

    def __init__(self, collection):
        """Initialize a RunFromText instance with rules collection."""
        self.collection = collection

    def _call_runner(self, path) -> List["MatchError"]:
        runner = Runner(self.collection, path)
        return runner.run()

    def run_playbook(self, playbook_text):
        """Lints received text as a playbook."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", prefix="playbook") as fp:
            fp.write(playbook_text)
            fp.flush()
            results = self._call_runner(fp.name)
        return results

    def run_role_tasks_main(self, tasks_main_text):
        """Lints received text as tasks."""
        role_path = tempfile.mkdtemp(prefix='role_')
        tasks_path = os.path.join(role_path, 'tasks')
        os.makedirs(tasks_path)
        with open(os.path.join(tasks_path, 'main.yml'), 'w') as fp:
            fp.write(tasks_main_text)
        results = self._call_runner(role_path)
        shutil.rmtree(role_path)
        return results

    def run_role_meta_main(self, meta_main_text):
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
        cwd: str = None,
        bin: str = None,
        env: Dict[str, str] = None) -> subprocess.CompletedProcess:
    """Run ansible-lint on a given path and returns its output."""
    if not bin:
        bin = sys.executable
        args = [sys.executable, "-m", "ansiblelint", *argv]
    else:
        args = [bin, *argv]

    return subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,  # needed when command is a list
        check=False,
        cwd=cwd,
        env=env,
        universal_newlines=True
    )
