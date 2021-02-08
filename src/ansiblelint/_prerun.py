import os
import subprocess
import sys
from typing import List, Optional

from packaging import version

from ansiblelint.config import ansible_collections_path, collection_list, options
from ansiblelint.constants import (
    ANSIBLE_MIN_VERSION,
    ANSIBLE_MISSING_RC,
    ANSIBLE_MOCKED_MODULE,
)


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

    _prepare_library_paths()
    _prepare_roles_path()


def _prepare_library_paths() -> None:
    """Configure ANSIBLE_LIBRARY."""
    library_paths: List[str] = []
    if 'ANSIBLE_LIBRARY' in os.environ:
        library_paths = os.environ['ANSIBLE_LIBRARY'].split(':')

    if os.path.exists("plugins/modules") and "plugins/modules" not in library_paths:
        library_paths.append("plugins/modules")

    if options.mock_modules:
        for module_name in options.mock_modules:
            _make_module_stub(module_name)
        if os.path.exists(".cache/collections"):
            collection_list.append(".cache/collections")
        if os.path.exists(".cache/modules"):
            library_paths.append(".cache/modules")

    _update_env('ANSIBLE_LIBRARY', library_paths)
    _update_env(ansible_collections_path(), collection_list)


def _make_module_stub(module_name: str) -> None:
    if "." not in module_name:
        os.makedirs(".cache/modules", exist_ok=True)
        _write_module_stub(
            filename=f".cache/modules/{module_name}.py", name=module_name
        )
    else:
        namespace, collection, module_file = module_name.split(".")
        path = f".cache/collections/ansible_collections/{ namespace }/{ collection }/plugins/modules"
        os.makedirs(path, exist_ok=True)
        _write_module_stub(
            filename=f"{path}/{module_file}.py",
            name=module_file,
            namespace=namespace,
            collection=collection,
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


def _update_env(varname: str, value: List[str]) -> None:
    """Update environment variable if needed."""
    if value:
        value_str = ":".join(value)
        if value_str != os.environ.get(varname, ""):
            os.environ[varname] = value_str
            print("Added %s=%s" % (varname, value_str), file=sys.stderr)


def _prepare_roles_path() -> None:
    """Configure ANSIBLE_ROLES_PATH."""
    roles_path: List[str] = []
    if 'ANSIBLE_ROLES_PATH' in os.environ:
        roles_path = os.environ['ANSIBLE_ROLES_PATH'].split(':')

    if os.path.exists("roles") and "roles" not in roles_path:
        roles_path.append("roles")

    if options.mock_roles or os.path.exists(".cache/roles"):
        for role_name in options.mock_roles:
            os.makedirs(f".cache/roles/{role_name}", exist_ok=True)
        if ".cache/roles" not in roles_path:
            roles_path.append(".cache/roles")

    if roles_path:
        roles_path_str = ":".join(roles_path)
        os.environ['ANSIBLE_ROLES_PATH'] = roles_path_str
        print("Added ANSIBLE_ROLES_PATH=%s" % roles_path_str, file=sys.stderr)
