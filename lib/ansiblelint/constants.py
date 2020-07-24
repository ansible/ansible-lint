"""Constants used by AnsibleLint."""
import os.path
import sys

# mypy needs this special condition or it may fail to run
# https://github.com/python/typeshed/issues/3500#issuecomment-560958608
if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

DEFAULT_RULESDIR = os.path.join(os.path.dirname(__file__), 'rules')

INVALID_CONFIG_RC = 2
ANSIBLE_FAILURE_RC = 3

FileType = Literal["playbook", "pre_tasks", "post_tasks"]
