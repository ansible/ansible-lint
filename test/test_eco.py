"""Test a set of 3rd party Ansible repositories for possible regressions."""
import os
import pathlib
import subprocess

import pytest

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
    subprocess.run(
        # we exclude `fqcn-builtins` until repository owners fix it.
        f'ansible-lint -f pep8 -x fqcn-builtins 2>&1 | sed "s:${{HOME}}:~:g" > {my_dir}/{repo}.result',
        shell=True,
        check=False,
        cwd=f"{cache_dir}/{repo}",
    )
    # fail if result is different than our expected one:
    subprocess.run(f"git diff HEAD test/eco/{repo}.result", shell=True, check=True)
