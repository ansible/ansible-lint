import os
import pathlib
import re
import subprocess
import sys
from functools import lru_cache
from typing import List, Optional, Tuple

from packaging import version

from ansiblelint.config import (
    ansible_collections_path,
    collection_list,
    options,
    parse_ansible_version,
)
from ansiblelint.constants import (
    ANSIBLE_DEFAULT_ROLES_PATH,
    ANSIBLE_MIN_VERSION,
    ANSIBLE_MISSING_RC,
    ANSIBLE_MOCKED_MODULE,
    INVALID_CONFIG_RC,
    INVALID_PREREQUISITES_RC,
)
from ansiblelint.loaders import yaml_from_file


def check_ansible_presence(exit_on_error: bool = False) -> Tuple[str, str]:
    """Assures we stop execution if Ansible is missing or outdated.

    Returne found version and an optional exception if something wrong
    was detected.
    """

    @lru_cache()
    def _get_ver_err() -> Tuple[str, str]:

        err = ""
        failed = False
        ver = ""
        result = subprocess.run(
            args=["ansible", "--version"],
            stdout=subprocess.PIPE,
            universal_newlines=True,
            check=False,
        )
        if result.returncode != 0:
            return (
                ver,
                "FATAL: Unable to retrieve ansible cli version: %s" % result.stdout,
            )

        ver, error = parse_ansible_version(result.stdout)
        if error is not None:
            return "", error
        try:
            # pylint: disable=import-outside-toplevel
            from ansible.release import __version__ as ansible_module_version

            if version.parse(ansible_module_version) < version.parse(
                ANSIBLE_MIN_VERSION
            ):
                failed = True
        except (ImportError, ModuleNotFoundError) as e:
            failed = True
            ansible_module_version = "none"
            err += f"{e}\n"
        if failed:
            err += (
                "FATAL: ansible-lint requires a version of Ansible package"
                " >= %s, but %s was found. "
                "Please install a compatible version using the same python interpreter. See "
                "https://docs.ansible.com/ansible/latest/installation_guide"
                "/intro_installation.html#installing-ansible-with-pip"
                % (ANSIBLE_MIN_VERSION, ansible_module_version)
            )

        elif ver != ansible_module_version:
            err = (
                f"FATAL: Ansible CLI ({ver}) and python module"
                f" ({ansible_module_version}) versions do not match. This "
                "indicates a broken execution environment."
            )
        return ver, err

    ver, err = _get_ver_err()
    if exit_on_error and err:
        print(err, file=sys.stderr)
        sys.exit(ANSIBLE_MISSING_RC)
    return ver, err


def prepare_environment() -> None:
    """Make dependencies available if needed."""
    if not options.offline and os.path.exists("requirements.yml"):

        cmd = [
            "ansible-galaxy",
            "role",
            "install",
            "--roles-path",
            f"{options.project_dir}/.cache/roles",
            "-vr",
            "requirements.yml",
        ]

        print("Running %s" % " ".join(cmd), file=sys.stderr)
        run = subprocess.run(
            cmd,
            universal_newlines=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if run.returncode != 0:
            print(run.stdout, file=sys.stderr)
            sys.exit(run.returncode)

        # Run galaxy collection install works on v2 requirements.yml
        if "collections" in yaml_from_file("requirements.yml"):

            cmd = [
                "ansible-galaxy",
                "collection",
                "install",
                "-p",
                f"{options.project_dir}/.cache/collections",
                "-vr",
                "requirements.yml",
            ]

            print("Running %s" % " ".join(cmd), file=sys.stderr)
            run = subprocess.run(
                cmd,
                universal_newlines=True,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            if run.returncode != 0:
                print(run.stdout, file=sys.stderr)
                sys.exit(run.returncode)

    _install_galaxy_role()
    _perform_mockings()
    _prepare_ansible_paths()


def _install_galaxy_role() -> None:
    """Detect standalone galaxy role and installs it."""
    if not os.path.exists("meta/main.yml"):
        return
    yaml = yaml_from_file("meta/main.yml")
    if 'galaxy_info' not in yaml:
        return
    role_name = yaml['galaxy_info'].get('role_name', None)
    role_author = yaml['galaxy_info'].get('author', None)
    if not role_name:
        role_name = pathlib.Path(".").absolute().name
        role_name = re.sub(r'^{0}'.format(re.escape('ansible-role-')), '', role_name)
    fqrn = f"{role_author}.{role_name}"
    if not re.match(r"[a-z0-9][a-z0-9_]+\.[a-z][a-z0-9_]+$", fqrn):
        print(
            f"""\
Computed fully qualified role name of {fqrn} is not valid.
Please edit meta/main.yml and assure we can correctly determine full role name:

galaxy_info:
  role_name: my_name  # if absent directory name hosting role is used instead
  author: my_galaxy_namespace

Namespace: https://galaxy.ansible.com/docs/contributing/namespaces.html#galaxy-namespace-limitations
Role: https://galaxy.ansible.com/docs/contributing/creating_role.html#role-names
""",
            file=sys.stderr,
        )
        sys.exit(INVALID_PREREQUISITES_RC)
    p = pathlib.Path(f"{options.project_dir}/.cache/roles")
    p.mkdir(parents=True, exist_ok=True)
    link_path = p / f"{role_author}.{role_name}"
    # despite documentation stating that is_file() reports true for symlinks,
    # it appears that is_dir() reports true instead, so we rely on exits().
    if not link_path.exists():
        link_path.symlink_to(pathlib.Path("../..", target_is_directory=True))
    print(
        f"Using {link_path} symlink to current repository in order to enable Ansible to find the role using its expected full name.",
        file=sys.stderr,
    )


def _prepare_ansible_paths() -> None:
    """Configure Ansible environment variables."""
    library_paths: List[str] = []
    roles_path: List[str] = []

    for path_list, path in (
        (library_paths, "plugins/modules"),
        (library_paths, f"{options.project_dir}/.cache/modules"),
        (collection_list, f"{options.project_dir}/.cache/collections"),
        (roles_path, "roles"),
        (roles_path, f"{options.project_dir}/.cache/roles"),
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
        path = f"{ options.project_dir }/.cache/collections/ansible_collections/{ namespace }/{ collection }/plugins/modules"
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
        os.makedirs(f"{options.project_dir}/.cache/modules", exist_ok=True)
        _write_module_stub(
            filename=f"{options.project_dir}/.cache/modules/{module_name}.py",
            name=module_name,
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

    # if inside a collection repo, symlink it to simulate its installed state
    if not os.path.exists("galaxy.yml"):
        return
    yaml = yaml_from_file("galaxy.yml")
    namespace = yaml.get('namespace', None)
    collection = yaml.get('name', None)
    if not namespace or not collection:
        return
    p = pathlib.Path(
        f"{options.project_dir}/.cache/collections/ansible_collections/{ namespace }"
    )
    p.mkdir(parents=True, exist_ok=True)
    link_path = p / collection
    if not link_path.exists():
        link_path.symlink_to(pathlib.Path("../../../..", target_is_directory=True))
