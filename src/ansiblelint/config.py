"""Store configuration options as a singleton."""
from __future__ import annotations

import json
import logging
import os
import sys
import time
import urllib.request
import warnings
from argparse import Namespace
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError

from packaging.version import Version

from ansiblelint import __version__
from ansiblelint.loaders import yaml_from_file

_logger = logging.getLogger(__name__)


CACHE_DIR = (
    os.path.expanduser(os.environ.get("XDG_CONFIG_CACHE", "~/.cache")) + "/ansible-lint"
)

DEFAULT_WARN_LIST = [
    "avoid-implicit",
    "experimental",
    "fqcn[action]",
    "fqcn[redirect]",
    "jinja[spacing]",  # warning until we resolve all reported false-positives
    "name[casing]",
    "name[play]",
    "name[prefix]",
    "role-name",
    "warning[empty-playbook]",  # because ansible considers it warning only
    "role-name[path]",  # too new
]

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
    {"inventory": "**/inventory/**.{yaml,yml}"},
    {"requirements": "**/meta/requirements.{yaml,yml}"},  # v1 only
    # https://docs.ansible.com/ansible/latest/dev_guide/collections_galaxy_meta.html
    {"galaxy": "**/galaxy.yml"},  # Galaxy collection meta
    {"reno": "**/releasenotes/*/*.{yaml,yml}"},  # reno release notes
    {"tasks": "**/tasks/**/*.{yaml,yml}"},
    {"playbook": "**/playbooks/*.{yml,yaml}"},
    {"playbook": "**/*playbook*.{yml,yaml}"},
    {"role": "**/roles/*/"},
    {"handlers": "**/handlers/*.{yaml,yml}"},
    {"vars": "**/{host_vars,group_vars,vars,defaults}/**/*.{yaml,yml}"},
    {"test-meta": "**/tests/integration/targets/*/meta/main.{yaml,yml}"},
    {"meta": "**/meta/main.{yaml,yml}"},
    {"meta-runtime": "**/meta/runtime.{yaml,yml}"},
    {"arg_specs": "**/meta/argument_specs.{yaml,yml}"},  # role argument specs
    {"yaml": ".config/molecule/config.{yaml,yml}"},  # molecule global config
    {
        "requirements": "**/molecule/*/{collections,requirements}.{yaml,yml}"
    },  # molecule old collection requirements (v1), ansible 2.8 only
    {"yaml": "**/molecule/*/{base,molecule}.{yaml,yml}"},  # molecule config
    {"requirements": "**/requirements.{yaml,yml}"},  # v2 and v1
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

PROFILES = yaml_from_file(Path(__file__).parent / "data" / "profiles.yml")

options = Namespace(
    cache_dir=None,
    colored=True,
    configured=False,
    cwd=".",
    display_relative_path=True,
    exclude_paths=[],
    format="rich",
    lintables=[],
    list_rules=False,
    list_tags=False,
    write_list=[],
    parseable=False,
    quiet=False,
    rulesdirs=[],
    skip_list=[],
    tags=[],
    verbosity=False,
    warn_list=[],
    kinds=DEFAULT_KINDS,
    mock_filters=[],
    mock_modules=[],
    mock_roles=[],
    loop_var_prefix=None,
    only_builtins_allow_collections=[],
    only_builtins_allow_modules=[],
    var_naming_pattern=None,
    offline=False,
    project_dir=".",  # default should be valid folder (do not use None here)
    extra_vars=None,
    enable_list=[],
    skip_action_validation=True,
    strict=False,
    rules={},  # Placeholder to set and keep configurations for each rule.
    profile=None,
    task_name_prefix="{stem} | ",
)

# Used to store detected tag deprecations
used_old_tags: dict[str, str] = {}

# Used to store collection list paths (with mock paths if needed)
collection_list: list[str] = []


def get_rule_config(rule_id: str) -> dict[str, Any]:
    """Get configurations for the rule ``rule_id``."""
    rule_config = options.rules.get(rule_id, {})
    if not isinstance(rule_config, dict):  # pragma: no branch
        raise RuntimeError(f"Invalid rule config for {rule_id}: {rule_config}")
    return rule_config


@lru_cache
def ansible_collections_path() -> str:
    """Return collection path variable for current version of Ansible."""
    # respect Ansible behavior, which is to load old name if present
    for env_var in [
        "ANSIBLE_COLLECTIONS_PATHS",
        "ANSIBLE_COLLECTIONS_PATH",
    ]:  # pragma: no cover
        if env_var in os.environ:
            return env_var
    return "ANSIBLE_COLLECTIONS_PATH"


def in_venv() -> bool:
    """Determine whether Python is running from a venv."""
    if hasattr(sys, "real_prefix") or os.environ.get("CONDA_EXE", None) is not None:
        return True

    pfx = getattr(sys, "base_prefix", sys.prefix)
    return pfx != sys.prefix


def guess_install_method() -> str:
    """Guess if pip upgrade command should be used."""
    package_name = "ansible-lint"
    pip = ""
    if in_venv():
        _logger.debug("Found virtualenv, assuming `pip3 install` will work.")
        pip = f"pip install --upgrade {package_name}"
    elif __file__.startswith(os.path.expanduser("~/.local/lib")):
        _logger.debug(
            "Found --user installation, assuming `pip3 install --user` will work."
        )
        pip = f"pip3 install --user --upgrade {package_name}"

    # By default we assume pip is not safe to be used
    use_pip = False
    try:
        # Use pip to detect if is safe to use it to upgrade the package.
        # We do imports here to for performance and reasons, and also in order
        # to avoid errors if pip internals change. Also we want to avoid having
        # to add pip as a dependency, so we make use of it only when present.

        # trick to avoid runtime warning from inside pip: _distutils_hack/__init__.py:33: UserWarning: Setuptools is replacing distutils.
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            # pylint: disable=import-outside-toplevel
            from pip._internal.metadata import get_default_environment
            from pip._internal.req.req_uninstall import uninstallation_paths

            dist = get_default_environment().get_distribution(package_name)
            if dist:
                logging.debug("Found %s dist", dist)
                for _ in uninstallation_paths(dist):
                    use_pip = True
            else:
                logging.debug("Skipping %s as it is not installed.", package_name)
                use_pip = False
    # pylint: disable=broad-except
    except Exception as exc:
        # On Fedora 36, we got a AttributeError exception from pip that we want to avoid
        logging.debug(exc)
        use_pip = False

    # We only want to recommend pip for upgrade if it looks safe to do so.
    return pip if use_pip else ""


def get_version_warning() -> str:
    """Display warning if current version is outdated."""
    # 0.1dev1 is special fallback version
    if __version__ == "0.1.dev1":  # pragma: no cover
        return ""

    msg = ""
    data = {}
    current_version = Version(__version__)

    if not os.path.exists(CACHE_DIR):  # pragma: no cover
        os.makedirs(CACHE_DIR)
    cache_file = f"{CACHE_DIR}/latest.json"
    refresh = True
    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < 24 * 60 * 60:
            refresh = False
        with open(cache_file, encoding="utf-8") as f:
            data = json.load(f)

    if refresh or not data:
        release_url = (
            "https://api.github.com/repos/ansible/ansible-lint/releases/latest"
        )
        try:
            with urllib.request.urlopen(release_url) as url:
                data = json.load(url)
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(data, f)
        except (URLError, HTTPError) as exc:  # pragma: no cover
            _logger.debug(
                "Unable to fetch latest version from %s due to: %s", release_url, exc
            )
            return ""

    html_url = data["html_url"]
    new_version = Version(data["tag_name"][1:])  # removing v prefix from tag

    if current_version > new_version:
        msg = "[dim]You are using a pre-release version of ansible-lint.[/]"
    elif current_version < new_version:
        msg = f"""[warning]A new release of ansible-lint is available: [red]{current_version}[/] → [green][link={html_url}]{new_version}[/][/][/]"""

        pip = guess_install_method()
        if pip:
            msg += f" Upgrade by running: [info]{pip}[/]"

    return msg
