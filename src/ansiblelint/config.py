"""Store configuration options as a singleton."""
import os
import subprocess
import sys
from argparse import Namespace
from functools import lru_cache
from typing import Dict, List

from packaging.version import Version

from ansiblelint.constants import ANSIBLE_MISSING_RC

DEFAULT_KINDS = [
    # Do not sort this list, order matters.
    {"requirements": "requirements.yml"},  # v2 and v1
    {"requirements": "**/meta/requirements.yml"},  # v1 only
    {"reno": "releasenotes/*/*.{yaml,yml}"},  # reno release notes
    {"playbook": "**/playbooks/*.{yml,yaml}"},
    {"playbook": "**/*playbook*.{yml,yaml}"},
    {"role": "**/roles/*/"},
    {"tasks": "**/tasks/*.{yaml,yml}"},
    {"handlers": "**/handlers/*.{yaml,yml}"},
    {"vars": "**/{vars,defaults}/*.{yaml,yml}"},
    {"meta": "**/meta/main.{yaml,yml}"},
    {"yaml": ".config/molecule/config.{yaml,yml}"},  # molecule global config
    {"yaml": "**/molecule/*/molecule.{yaml,yml}"},  # molecule config
    {"playbook": "**/molecule/*/*.{yaml,yml}"},  # molecule playbooks
    {"yaml": "**/*.{yaml,yml}"},
    {"yaml": "**/.*.{yaml,yml}"},
]

options = Namespace(
    colored=True,
    cwd=".",
    display_relative_path=True,
    exclude_paths=[],
    lintables=[],
    listrules=False,
    listtags=False,
    parseable=False,
    parseable_severity=False,
    quiet=False,
    rulesdirs=[],
    skip_list=[],
    tags=[],
    verbosity=False,
    warn_list=[],
    kinds=DEFAULT_KINDS,
    mock_modules=[],
    mock_roles=[],
    loop_var_prefix=None,
    offline=False,
)

# Used to store detected tag deprecations
used_old_tags: Dict[str, str] = {}

# Used to store collection list paths (with mock paths if needed)
collection_list: List[str] = []


@lru_cache()
def ansible_collections_path() -> str:
    """Return collection path variable for current version of Ansible."""
    # respect Ansible behavior, which is to load old name if present
    for env_var in ["ANSIBLE_COLLECTIONS_PATHS", "ANSIBLE_COLLECTIONS_PATH"]:
        if "ANSIBLE_COLLECTIONS_PATHS" in os.environ:
            return env_var

    # https://github.com/ansible/ansible/pull/70007
    if ansible_version() >= ansible_version("2.10.0.dev0"):
        return "ANSIBLE_COLLECTIONS_PATH"
    return "ANSIBLE_COLLECTIONS_PATHS"


@lru_cache()
def ansible_version(version: str = "") -> Version:
    """Return current Version object for Ansible.

    If version is not mentioned, it returns current version as detected.
    When version argument is mentioned, it return converts the version string
    to Version object in order to make it usable in comparisons.
    """
    if not version:
        proc = subprocess.run(
            ["ansible", "--version"],
            universal_newlines=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if proc.returncode == 0:
            version = proc.stdout.splitlines()[0].split()[1]
        else:
            print(
                "Unable to find a working copy of ansible executable.",
                proc,
            )
            sys.exit(ANSIBLE_MISSING_RC)
    return Version(version)


if ansible_collections_path() in os.environ:
    collection_list = os.environ[ansible_collections_path()].split(':')
