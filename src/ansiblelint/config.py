"""Store configuration options as a singleton."""
import os
import re
import subprocess
import sys
from argparse import Namespace
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from packaging.version import Version

from ansiblelint.constants import ANSIBLE_MISSING_RC

DEFAULT_KINDS = [
    # Do not sort this list, order matters.
    {"jinja2": "**/*.j2"},  # jinja2 templates are not always parsable as something else
    {"jinja2": "**/*.j2.*"},
    {"inventory": "**/inventory/**.yml"},
    {"requirements": "**/meta/requirements.yml"},  # v1 only
    # https://docs.ansible.com/ansible/latest/dev_guide/collections_galaxy_meta.html
    {"galaxy": "**/galaxy.yml"},  # Galaxy collection meta
    {"reno": "**/releasenotes/*/*.{yaml,yml}"},  # reno release notes
    {"playbook": "**/playbooks/*.{yml,yaml}"},
    {"playbook": "**/*playbook*.{yml,yaml}"},
    {"role": "**/roles/*/"},
    {"tasks": "**/tasks/**/*.{yaml,yml}"},
    {"handlers": "**/handlers/*.{yaml,yml}"},
    {"vars": "**/{host_vars,group_vars,vars,defaults}/**/*.{yaml,yml}"},
    {"meta": "**/meta/main.{yaml,yml}"},
    {"yaml": ".config/molecule/config.{yaml,yml}"},  # molecule global config
    {
        "requirements": "**/molecule/*/{collections,requirements}.{yaml,yml}"
    },  # molecule old collection requirements (v1), ansible 2.8 only
    {"yaml": "**/molecule/*/{base,molecule}.{yaml,yml}"},  # molecule config
    {"requirements": "**/requirements.yml"},  # v2 and v1
    {"playbook": "**/molecule/*/*.{yaml,yml}"},  # molecule playbooks
    {"yaml": "**/{.ansible-lint,.yamllint}"},
    {"yaml": "**/*.{yaml,yml}"},
    {"yaml": "**/.*.{yaml,yml}"},
]

BASE_KINDS = [
    # These assignations are only for internal use and are only inspired by
    # MIME/IANA model. Their purpose is to be able to process a file based on
    # it type, including generic processing of text files using the prefix.
    {
        "text/jinja2": "**/*.j2"
    },  # jinja2 templates are not always parsable as something else
    {"text/jinja2": "**/*.j2.*"},
    {"text": "**/templates/**/*.*"},  # templates are likely not validable
    {"text/json": "**/*.json"},  # standardized
    {"text/markdown": "**/*.md"},  # https://tools.ietf.org/html/rfc7763
    {"text/rst": "**/*.rst"},  # https://en.wikipedia.org/wiki/ReStructuredText
    {"text/ini": "**/*.ini"},
    # YAML has no official IANA assignation
    {"text/yaml": "**/{.ansible-lint,.yamllint}"},
    {"text/yaml": "**/*.{yaml,yml}"},
    {"text/yaml": "**/.*.{yaml,yml}"},
]


options = Namespace(
    cache_dir=None,
    colored=True,
    configured=False,
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
    var_naming_pattern=None,
    offline=False,
    project_dir=".",  # default should be valid folder (do not use None here)
    extra_vars=None,
    enable_list=[],
    skip_action_validation=True,
    rules=dict(),  # Placeholder to set and keep configurations for each rule.
)

# Used to store detected tag deprecations
used_old_tags: Dict[str, str] = {}

# Used to store collection list paths (with mock paths if needed)
collection_list: List[str] = []


def get_rule_config(rule_id: str) -> Dict[str, Any]:
    """Get configurations for the rule ``rule_id``."""
    rule_config = options.rules.get(rule_id, dict())
    if not isinstance(rule_config, dict):
        raise RuntimeError("Invalid rule config for %s: %s" % (rule_id, rule_config))
    return rule_config


@lru_cache()
def ansible_collections_path() -> str:
    """Return collection path variable for current version of Ansible."""
    # respect Ansible behavior, which is to load old name if present
    for env_var in ["ANSIBLE_COLLECTIONS_PATHS", "ANSIBLE_COLLECTIONS_PATH"]:
        if env_var in os.environ:
            return env_var

    # https://github.com/ansible/ansible/pull/70007
    if ansible_version() >= ansible_version("2.10.0.dev0"):
        return "ANSIBLE_COLLECTIONS_PATH"
    return "ANSIBLE_COLLECTIONS_PATHS"


def parse_ansible_version(stdout: str) -> Tuple[str, Optional[str]]:
    """Parse output of 'ansible --version'."""
    # Ansible can produce extra output before displaying version in debug mode.

    # ansible-core 2.11+: 'ansible [core 2.11.3]'
    match = re.search(r"^ansible \[(?:core|base) ([^\]]+)\]", stdout, re.MULTILINE)
    if match:
        return match.group(1), None
    # ansible-base 2.10 and Ansible 2.9: 'ansible 2.x.y'
    match = re.search(r"^ansible ([^\s]+)", stdout, re.MULTILINE)
    if match:
        return match.group(1), None
    return "", "FATAL: Unable parse ansible cli version: %s" % stdout


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
            version, error = parse_ansible_version(proc.stdout)
            if error is not None:
                print(error)
                sys.exit(ANSIBLE_MISSING_RC)
        else:
            print(
                "Unable to find a working copy of ansible executable.",
                proc,
            )
            sys.exit(ANSIBLE_MISSING_RC)
    return Version(version)


if ansible_collections_path() in os.environ:
    collection_list = os.environ[ansible_collections_path()].split(':')
