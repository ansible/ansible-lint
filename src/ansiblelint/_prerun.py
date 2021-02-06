import os
import subprocess
import sys
from typing import List

from packaging import version

from ansiblelint.config import options
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
    """Make custom modules available if needed."""
    if os.path.exists("requirements.yml"):

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

        if 'ANSIBLE_COLLECTIONS_PATHS' in os.environ:
            os.environ[
                'ANSIBLE_COLLECTIONS_PATHS'
            ] = f".cache/collections:{os.environ['ANSIBLE_COLLECTIONS_PATHS']}"
        else:
            os.environ['ANSIBLE_COLLECTIONS_PATHS'] = ".cache/collections"

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
        library_paths.append(".cache/modules")
        os.makedirs(".cache/modules", exist_ok=True)
        for module_name in options.mock_modules:
            with open(f".cache/modules/{module_name}.py", "w") as f:
                f.write(ANSIBLE_MOCKED_MODULE)

    library_path_str = ":".join(library_paths)
    if library_path_str != os.environ.get('ANSIBLE_LIBRARY', ""):
        os.environ['ANSIBLE_LIBRARY'] = library_path_str
        print("Added ANSIBLE_LIBRARY=%s" % library_path_str, file=sys.stderr)


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
