"""Test a set of 3rd party Ansible repositories for possible regressions."""
import os
import pathlib
import re
import shlex
import subprocess

import pytest

from ansiblelint.testing import run_ansible_lint

eco_repos = {
    "bootstrap": [
        "https://github.com/robertdebock/ansible-role-bootstrap",
        "robertdebock",
    ],
    "colsystem": [
        "https://github.com/devroles/ansible_collection_system",
        "greg-hellings",
    ],
    "debops": ["https://github.com/debops/debops", "drybjed"],
    "docker-rootless": [
        "https://github.com/konstruktoid/ansible-docker-rootless",
        "konstruktoid",
    ],
    "tripleo-ansible": ["https://opendev.org/openstack/tripleo-ansible", "ssbarnea"],
    "hardening": [
        "https://github.com/konstruktoid/ansible-role-hardening",
        "konstruktoid",
    ],
    "mysql": [
        "https://github.com/geerlingguy/ansible-role-mysql.git",
        "geerlingguy",
    ],
    "zuul-jobs": ["https://opendev.org/zuul/zuul-jobs", "ssbarnea"],
}


@pytest.mark.eco()
@pytest.mark.parametrize(("repo"), (eco_repos.keys()))
def test_eco(repo: str) -> None:
    """Test a set of 3rd party Ansible repositories for possible regressions."""
    url = eco_repos[repo][0]
    cache_dir = os.path.expanduser("~/.cache/ansible-lint-eco")
    my_dir = (pathlib.Path(__file__).parent / "eco").resolve()
    os.makedirs(cache_dir, exist_ok=True)
    # clone repo
    if os.path.exists(f"{cache_dir}/{repo}/.git"):
        subprocess.run("git pull", cwd=f"{cache_dir}/{repo}", shell=True, check=True)
    else:
        subprocess.run(f"git clone {url} {cache_dir}/{repo}", shell=True, check=True)
    # run ansible lint and paths from user home in order to produce
    # consistent results regardless on its location.

    # we exclude `fqcn-builtins` until repository owners fix it.
    args = ["-f", "pep8", "-x", "fqcn-builtins"]
    result = run_ansible_lint(
        *args,
        executable="ansible-lint",
        cwd=f"{cache_dir}/{repo}",
    )

    def sanitize_output(text: str) -> str:
        """Make the output less likely to vary between runs or minor changes."""
        # replace full path to home directory with ~.
        result = text.replace(os.path.expanduser("~"), "~")
        # removes summary line it can change too often on active repositories.
        result = re.sub(r"^Finished with .+\n", "", result, flags=re.MULTILINE)

        return result

    result_txt = f"CMD: {shlex.join(result.args)}\n\nRC: {result.returncode}\n\nSTDERR:\n{result.stderr}\n\nSTDOUT:\n{result.stdout}"

    with open(f"{my_dir}/{repo}.result", "w", encoding="utf-8") as f:
        f.write(sanitize_output(result_txt))
    # fail if result is different than our expected one:
    result = subprocess.run(
        f"git diff --exit-code test/eco/{repo}.result",
        shell=True,
        check=False,
        capture_output=True,
    )
    assert result.returncode == 0, result_txt
