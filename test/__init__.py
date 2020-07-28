"""Test suite for ansible-lint."""

import os
import shutil
import subprocess
import sys
import tempfile
from typing import Dict

from ansible import __version__ as ansible_version_str

from ansiblelint.runner import Runner

ANSIBLE_MAJOR_VERSION = tuple(map(int, ansible_version_str.split('.')[:2]))


class RunFromText(object):
    """Use Runner on temp files created from unittest text snippets."""

    def __init__(self, collection):
        """Initialize a RunFromText instance with rules collection."""
        self.collection = collection

    def _call_runner(self, path):
        runner = Runner(self.collection, path, [], [], [])
        return runner.run()

    def run_playbook(self, playbook_text):
        play_root = tempfile.mkdtemp()
        with open(os.path.join(play_root, 'playbook.yml'), 'w') as fp:
            fp.write(playbook_text)
        results = self._call_runner(fp.name)
        shutil.rmtree(play_root)
        return results

    def run_role_tasks_main(self, tasks_main_text):
        role_path = tempfile.mkdtemp(prefix='role_')
        tasks_path = os.path.join(role_path, 'tasks')
        os.makedirs(tasks_path)
        with open(os.path.join(tasks_path, 'main.yml'), 'w') as fp:
            fp.write(tasks_main_text)
        results = self._call_runner(role_path)
        shutil.rmtree(role_path)
        return results

    def run_role_meta_main(self, meta_main_text):
        role_path = tempfile.mkdtemp(prefix='role_')
        meta_path = os.path.join(role_path, 'meta')
        os.makedirs(meta_path)
        with open(os.path.join(meta_path, 'main.yml'), 'w') as fp:
            fp.write(meta_main_text)
        results = self._call_runner(role_path)
        shutil.rmtree(role_path)
        return results


def run_ansible_lint(
        cwd: os.PathLike = None,
        role_path: os.PathLike = None,
        bin: str = None,
        env: Dict[str, str] = None):
    """Run ansible-lint on a given path and returns its output."""
    if bin:
        command = [bin, "-v"]
    else:
        command = [sys.executable, "-m", "ansiblelint", "-v"]
    if role_path:
        command.append(role_path)

    result, err = subprocess.Popen(
        command,
        cwd=cwd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,  # needed when command is a list
        env=env,
    ).communicate()

    return result
