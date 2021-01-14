import os
import subprocess
import sys

from packaging import version

from ansiblelint.constants import ANSIBLE_MIN_VERSION, ANSIBLE_MISSING_RC


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
            "/intro_installation.html#installing-ansible-with-pip" %
            (ANSIBLE_MIN_VERSION, __version__), file=sys.stderr)
        sys.exit(ANSIBLE_MISSING_RC)


def prepare_environment() -> None:
    """Make custom modules available if needed."""
    if os.path.exists("plugins/modules") and 'ANSIBLE_LIBRARY' not in os.environ:
        os.environ['ANSIBLE_LIBRARY'] = "plugins/modules"
        print("Added ANSIBLE_LIBRARY=plugins/modules", file=sys.stderr)

    if os.path.exists("roles") and "ANSIBLE_ROLES_PATH" not in os.environ:
        os.environ['ANSIBLE_ROLES_PATH'] = "roles"
        print("Added ANSIBLE_ROLES_PATH=roles", file=sys.stderr)

    if os.path.exists("requirements.yml"):

        cmd = [
            "ansible-galaxy",
            "install",
            "--roles-path",
            ".cache/roles",
            "-vr",
            "requirements.yml"
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
            "requirements.yml"
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

        if 'ANSIBLE_ROLES_PATH' in os.environ:
            os.environ['ANSIBLE_ROLES_PATH'] = f".cache/roles:{os.environ['ANSIBLE_ROLES_PATH']}"
        if 'ANSIBLE_COLLECTIONS_PATHS' in os.environ:
            os.environ['ANSIBLE_COLLECTIONS_PATHS'] = \
                f".cache/collections:{os.environ['ANSIBLE_COLLECTIONS_PATHS']}"
        else:
            os.environ['ANSIBLE_COLLECTIONS_PATHS'] = ".cache/collections"


check_ansible_presence()
prepare_environment()
