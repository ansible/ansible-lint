"""Test for the --progressive mode."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from ansiblelint.file_utils import cwd

FAULTY_PLAYBOOK = """---
- name: faulty
  hosts: localhost
  tasks:
    - name: hello
      debug:
        msg: world
"""

CORRECT_PLAYBOOK = """---
- name: Correct
  hosts: localhost
  tasks:
    - name: Hello
      ansible.builtin.debug:
        msg: world
"""


def git_init() -> None:
    """Init temporary git repository."""
    subprocess.run(["git", "init", "--initial-branch=main"], check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "config", "user.name", "test"], check=True)


def git_commit(filename: Path, content: str) -> None:
    """Create and commit a file."""
    filename.write_text(content)
    subprocess.run(["git", "add", filename], check=True)
    subprocess.run(["git", "commit", "-a", "-m", f"Commit {filename}"], check=True)


def run_lint(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    """Run ansible-lint."""
    # pylint: disable=subprocess-run-check
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )


def test_validate_progressive_mode_json_output(tmp_path: Path) -> None:
    """Test that covers the following scenarios for progressive mode.

    1. JSON output is valid in quiet and verbose modes
    2. New files are correctly handled whether lintable paths are passed or not
    3. Regression is not reported when the last commit doesn't add any new violations
    """
    cmd = [
        sys.executable,
        "-m",
        "ansiblelint",
        "--progressive",
        "-f",
        "json",
    ]
    with cwd(tmp_path):
        git_init()
        git_commit(tmp_path / "README.md", "pytest")
        git_commit(tmp_path / "playbook-faulty.yml", FAULTY_PLAYBOOK)
        cmd.append("-q")
        res = run_lint(cmd)
        assert res.returncode == 2
        json.loads(res.stdout)

        git_commit(tmp_path / "playbook-correct.yml", CORRECT_PLAYBOOK)
        cmd.extend(["-vv", "playbook-correct.yml"])
        res = run_lint(cmd)
        assert res.returncode == 0
        json.loads(res.stdout)
