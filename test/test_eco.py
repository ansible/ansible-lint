"""Test a set of 3rd party Ansible repositories for possible regressions."""
import os
import pathlib
import re
import shlex
import subprocess

import pytest

from ansiblelint.testing import run_ansible_lint

eco_repos = {
    "bootstrap": "https://github.com/robertdebock/ansible-role-bootstrap",
    "cisco.nxos": "https://github.com/ansible-collections/cisco.nxos",
    "colsystem": "https://github.com/devroles/ansible_collection_system",
    "debops": "https://github.com/debops/debops",
    "docker-rootless": "https://github.com/konstruktoid/ansible-docker-rootless",
    "hardening": "https://github.com/konstruktoid/ansible-role-hardening",
    "mysql": "https://github.com/geerlingguy/ansible-role-mysql.git",
    "tripleo-ansible": "https://opendev.org/openstack/tripleo-ansible",
    "zuul-jobs": "https://opendev.org/zuul/zuul-jobs",
}


def sanitize_output(text: str) -> str:
    """Make the output less likely to vary between runs or minor changes."""
    # replace full path to home directory with ~.
    result = text.replace(os.path.expanduser("~"), "~")
    # removes warning related to PATH alteration
    result = re.sub(
        r"^WARNING: PATH altered to include.+\n", "", result, flags=re.MULTILINE
    )

    return result


@pytest.mark.eco()
@pytest.mark.parametrize(("repo"), (eco_repos.keys()))
def test_eco(repo: str) -> None:
    """Test a set of 3rd party Ansible repositories for possible regressions."""
    url = eco_repos[repo]
    cache_dir = os.path.expanduser("~/.cache/ansible-lint-eco")
    my_dir = (pathlib.Path(__file__).parent / "eco").resolve()
    os.makedirs(cache_dir, exist_ok=True)
    # clone repo
    if os.path.exists(f"{cache_dir}/{repo}/.git"):
        subprocess.run("git pull", cwd=f"{cache_dir}/{repo}", shell=True, check=True)
    else:
        subprocess.run(
            f"git clone --recurse-submodules {url} {cache_dir}/{repo}",
            shell=True,
            check=True,
        )
    # run ansible lint and paths from user home in order to produce
    # consistent results regardless on its location.
    for step in ["before", "after"]:

        args = ["-f", "pep8"]
        executable = (
            "ansible-lint"
            if step == "after"
            else f"{pathlib.Path(__file__).parent.parent}/.tox/venv/bin/ansible-lint"
        )
        result = run_ansible_lint(
            *args,
            executable=executable,
            cwd=f"{cache_dir}/{repo}",
        )

        # Ensure that cmd looks the same for later diff, even if the path was different
        result.args[0] = "ansible-lint"
        # sort stderr because parallel runs can
        result.stderr = "\n".join(sorted(result.stderr.split("\n")))

        result_txt = f"CMD: {shlex.join(result.args)}\n\nRC: {result.returncode}\n\nSTDERR:\n{result.stderr}\n\nSTDOUT:\n{result.stdout}"

        os.makedirs(f"{my_dir}/{step}", exist_ok=True)
        with open(f"{my_dir}/{step}/{repo}.result", "w", encoding="utf-8") as f:
            f.write(sanitize_output(result_txt))

    # fail if result is different than our expected one
    result = subprocess.run(
        f"git --no-pager diff --exit-code --no-index test/eco/before/{repo}.result test/eco/after/{repo}.result",
        shell=True,
        check=False,
        capture_output=True,
    )
    assert result.returncode == 0, result_txt
