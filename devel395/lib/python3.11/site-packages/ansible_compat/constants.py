"""Constants used by ansible_compat."""


# Minimal version of Ansible we support for runtime
ANSIBLE_MIN_VERSION = "2.12"

# Based on https://docs.ansible.com/ansible/latest/reference_appendices/config.html
ANSIBLE_DEFAULT_ROLES_PATH = (
    "~/.ansible/roles:/usr/share/ansible/roles:/etc/ansible/roles"
)

INVALID_CONFIG_RC = 2
ANSIBLE_MISSING_RC = 4
INVALID_PREREQUISITES_RC = 10

MSG_INVALID_FQRL = """\
Computed fully qualified role name of {0} does not follow current galaxy requirements.
Please edit meta/main.yml and assure we can correctly determine full role name:

galaxy_info:
role_name: my_name  # if absent directory name hosting role is used instead
namespace: my_galaxy_namespace  # if absent, author is used instead

Namespace: https://galaxy.ansible.com/docs/contributing/namespaces.html#galaxy-namespace-limitations
Role: https://galaxy.ansible.com/docs/contributing/creating_role.html#role-names

As an alternative, you can add 'role-name' to either skip_list or warn_list.
"""
