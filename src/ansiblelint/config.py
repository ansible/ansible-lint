"""Store configuration options as a singleton."""
import os
import re
from argparse import Namespace
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_KINDS = [
    # Do not sort this list, order matters.
    {"jinja2": "**/*.j2"},  # jinja2 templates are not always parsable as something else
    {"jinja2": "**/*.j2.*"},
    {"yaml": ".github/**/*.{yaml,yml}"},  # github workflows
    {"text": "**/templates/**/*.*"},  # templates are likely not validable
    {"execution-environment": "**/execution-environment.yml"},
    {"ansible-lint-config": "**/.ansible-lint"},
    {"ansible-lint-config": "**/.config/ansible-lint.yml"},
    {"ansible-navigator-config": "**/ansible-navigator.{yaml,yml}"},
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
    {"test-meta": "**/tests/integration/targets/*/meta/main.{yaml,yml}"},
    {"meta": "**/meta/main.{yaml,yml}"},
    {"meta-runtime": "**/meta/runtime.{yaml,yml}"},
    {"arg_specs": "**/roles/**/meta/argument_specs.{yaml,yml}"},  # role argument specs
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


# Maps kinds to JSON schemas
# See https://www.schemastore.org/json/
JSON_SCHEMAS = {
    # Do not use anchors in these URLs because python-jsonschema does not support them:
    "playbook": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-playbook.json",
    "tasks": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-tasks.json",
    "vars": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-vars.json",
    "requirements": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-requirements.json",
    "meta": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-meta.json",
    "galaxy": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-galaxy.json",
    "execution-environment": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-ee.json",
    "meta-runtime": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-meta-runtime.json",
    "inventory": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-inventory.json",
    "ansible-lint-config": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-lint.json",
    "ansible-navigator-config": "https://raw.githubusercontent.com/ansible/ansible-navigator/main/src/ansible_navigator/data/ansible-navigator.json",
    "arg_specs": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-argument-specs.json",
}

options = Namespace(
    cache_dir=None,
    colored=True,
    configured=False,
    cwd=".",
    display_relative_path=True,
    exclude_paths=[],
    format="rich",
    lintables=[],
    listrules=False,
    listtags=False,
    write_list=[],
    parseable=False,
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
    rules={},  # Placeholder to set and keep configurations for each rule.
)

# Used to store detected tag deprecations
used_old_tags: Dict[str, str] = {}

# Used to store collection list paths (with mock paths if needed)
collection_list: List[str] = []


def get_rule_config(rule_id: str) -> Dict[str, Any]:
    """Get configurations for the rule ``rule_id``."""
    rule_config = options.rules.get(rule_id, {})
    if not isinstance(rule_config, dict):
        raise RuntimeError(f"Invalid rule config for {rule_id}: {rule_config}")
    return rule_config


@lru_cache()
def ansible_collections_path() -> str:
    """Return collection path variable for current version of Ansible."""
    # respect Ansible behavior, which is to load old name if present
    for env_var in ["ANSIBLE_COLLECTIONS_PATHS", "ANSIBLE_COLLECTIONS_PATH"]:
        if env_var in os.environ:
            return env_var
    return "ANSIBLE_COLLECTIONS_PATH"


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
    return "", f"FATAL: Unable parse ansible cli version: {stdout}"
