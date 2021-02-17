import os
import pathlib
import re
import subprocess
import sys
from typing import List, Optional

from packaging import version

from ansiblelint.config import ansible_collections_path, collection_list, options
from ansiblelint.constants import (
    ANSIBLE_DEFAULT_ROLES_PATH,
    ANSIBLE_MIN_VERSION,
    ANSIBLE_MISSING_RC,
    ANSIBLE_MOCKED_MODULE,
    INVALID_CONFIG_RC,
    INVALID_PREREQUISITES_RC,
)
from ansiblelint.loaders import yaml_from_file

MISSING_GALAXY_NAMESPACE = """\
A valid role namespace is required, edit meta/main.yml and assure that
author field is also a valid namespace:

galaxy_info:
  author: your_galaxy_namespace

See: https://galaxy.ansible.com/docs/contributing/namespaces.html#galaxy-namespace-limitations
"""


def check_ansible_presence() -> None:
    """Assures we stop execution if Ansible is missing."""
    failed = False
    try:
        # pylint: disable=import-outside-toplevel
        from ansible import release

        if version.parse(release.__version__) <= version.parse(ANSIBLE_MIN_VERSION):
            failed = True
    except (ImportError, ModuleNotFoundError) as e:
        failed = True
        __version__ = "none"
        print(e, file=sys.stderr)
    if failed:
        print(
            "FATAL: ansible-lint requires a version of Ansible package"
            " >= %s, but %s was found. "
            "Please install a compatible version using the same python interpreter. See "
            "https://docs.ansible.com/ansible/latest/installation_guide"
            "/intro_installation.html#installing-ansible-with-pip"
            % (ANSIBLE_MIN_VERSION, __version__),
            file=sys.stderr,
        )
        sys.exit(ANSIBLE_MISSING_RC)


def prepare_environment() -> None:
    """Make dependencies available if needed."""
    if not options.offline and os.path.exists("requirements.yml"):

        cmd = [
            "ansible-galaxy",
            "install",
            "--roles-path",
            ".cache/roles",
            "-vr",
            "requirements.yml",
        ]

        print("Running %s" % " ".join(cmd))
        run = subprocess.run(
            cmd,
            universal_newlines=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if run.returncode != 0:
            sys.exit(run.returncode)

        cmd = [
            "ansible-galaxy",
            "collection",
            "install",
            "-p",
            ".cache/collections",
            "-vr",
            "requirements.yml",
        ]

        print("Running %s" % " ".join(cmd))
        run = subprocess.run(
            cmd,
            universal_newlines=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if run.returncode != 0:
            sys.exit(run.returncode)

    _install_galaxy_role()
    _perform_mockings()
    _prepare_ansible_paths()


def _install_galaxy_role() -> None:
    """Detect standalone galaxy role and installs it."""
    if not os.path.exists("meta/main.yml"):
        return
    yaml = yaml_from_file("meta/main.yml")
    if 'galaxy_info' not in 'yaml':
        return
    role_name = yaml['galaxy_info'].get('role_name', None)
    role_author = yaml['galaxy_info'].get('author', None)
    if not role_name:
        role_name = os.path.dirname(".")
        role_name = re.sub(r'^{0}'.format(re.escape('ansible-role-')), '', role_name)
    if not role_author or not re.match(r"[\w\d_]{2,}", role_name):
        print(MISSING_GALAXY_NAMESPACE, file=sys.stderr)
        sys.exit(INVALID_PREREQUISITES_RC)
    p = pathlib.Path(".cache/roles")
    p.mkdir(parents=True, exist_ok=True)
    link_path = p / f"{role_author}.{role_name}"
    if not link_path.exists:
        link_path.symlink_to(pathlib.Path("../..", target_is_directory=True))


def _prepare_ansible_paths() -> None:
    """Configure Ansible environment variables."""
    library_paths: List[str] = []
    roles_path: List[str] = []

    for path_list, path in (
        (library_paths, "plugins/modules"),
        (library_paths, ".cache/modules"),
        (collection_list, ".cache/collections"),
        (roles_path, "roles"),
        (roles_path, ".cache/roles"),
    ):
        if path not in path_list and os.path.exists(path):
            path_list.append(path)

    _update_env('ANSIBLE_LIBRARY', library_paths)
    _update_env(ansible_collections_path(), collection_list)
    _update_env('ANSIBLE_ROLES_PATH', roles_path, default=ANSIBLE_DEFAULT_ROLES_PATH)


def _make_module_stub(module_name: str) -> None:
    # a.b.c is treated a collection
    if re.match(r"\w+\.\w+\.\w+", module_name):
        namespace, collection, module_file = module_name.split(".")
        path = f".cache/collections/ansible_collections/{ namespace }/{ collection }/plugins/modules"
        os.makedirs(path, exist_ok=True)
        _write_module_stub(
            filename=f"{path}/{module_file}.py",
            name=module_file,
            namespace=namespace,
            collection=collection,
        )
    elif "." in module_name:
        print(
            "Config error: %s is not a valid module name." % module_name,
            file=sys.stderr,
        )
        sys.exit(INVALID_CONFIG_RC)
    else:
        os.makedirs(".cache/modules", exist_ok=True)
        _write_module_stub(
            filename=f".cache/modules/{module_name}.py", name=module_name
        )


def _write_module_stub(
    filename: str,
    name: str,
    namespace: Optional[str] = None,
    collection: Optional[str] = None,
) -> None:
    """Write module stub to disk."""
    body = ANSIBLE_MOCKED_MODULE.format(
        name=name, collection=collection, namespace=namespace
    )
    with open(filename, "w") as f:
        f.write(body)


def _update_env(varname: str, value: List[str], default: str = "") -> None:
    """Update colon based environment variable if needed. by appending."""
    if value:
        value = [*os.environ.get(varname, default=default).split(':'), *value]
        value_str = ":".join(value)
        if value_str != os.environ.get(varname, ""):
            os.environ[varname] = value_str
            print("Added %s=%s" % (varname, value_str), file=sys.stderr)


def _perform_mockings() -> None:
    """Mock modules and roles."""
    for role_name in options.mock_roles:
        if re.match(r"\w+\.\w+\.\w+", role_name):
            namespace, collection, role_dir = role_name.split(".")
            path = f".cache/collections/ansible_collections/{ namespace }/{ collection }/roles/{ role_dir }/"
        else:
            path = f".cache/roles/{role_name}"
        os.makedirs(path, exist_ok=True)

    if options.mock_modules:
        for module_name in options.mock_modules:
            _make_module_stub(module_name)
