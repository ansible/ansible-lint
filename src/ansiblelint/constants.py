"""Constants used by AnsibleLint."""
import os.path
import sys

# mypy/pylint idiom for py36-py38 compatibility
# https://github.com/python/typeshed/issues/3500#issuecomment-560958608
if sys.version_info >= (3, 8):
    from typing import Literal  # pylint: disable=no-name-in-module
else:
    from typing_extensions import Literal

DEFAULT_RULESDIR = os.path.join(os.path.dirname(__file__), 'rules')
CUSTOM_RULESDIR_ENVVAR = "ANSIBLE_LINT_CUSTOM_RULESDIR"

INVALID_CONFIG_RC = 2
ANSIBLE_FAILURE_RC = 3
ANSIBLE_MISSING_RC = 4

# Minimal version of Ansible we support for runtime
ANSIBLE_MIN_VERSION = "2.9"

ANSIBLE_MOCKED_MODULE = """\
# This is a mocked Ansible module
from ansible.module_utils.basic import AnsibleModule


def main():
    return AnsibleModule(
        argument_spec=dict(
            data=dict(default=None),
            path=dict(default=None, type=str),
            file=dict(default=None, type=str),
        )
    )
"""

FileType = Literal[
    "playbook",
    "pre_tasks",
    "post_tasks",
    "meta",  # role meta
    "tasks",
    "handlers",
    # https://docs.ansible.com/ansible/latest/galaxy/user_guide.html#installing-roles-and-collections-from-the-same-requirements-yml-file
    "requirements",
    "role",  # that is a folder!
    "yaml",  # generic yaml file, previously reported as unknown file type
    ]


# odict is the base class used to represent data model of Ansible
# playbooks and tasks.
odict = dict
if sys.version_info[:2] < (3, 7):
    try:
        # pylint: disable=unused-import
        from collections import OrderedDict as odict  # noqa: 401
    except ImportError:
        pass
