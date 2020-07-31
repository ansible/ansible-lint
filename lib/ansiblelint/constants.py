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

FileType = Literal["playbook", "pre_tasks", "post_tasks"]
