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


check_ansible_presence()
