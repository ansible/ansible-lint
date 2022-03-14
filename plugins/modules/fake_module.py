"""Sample custom ansible module named fake_module.

This is used to test ability to detect and use custom modules.
"""
from ansible.module_utils.basic import AnsibleModule


def main() -> None:
    """Return the module instance."""
    return AnsibleModule(
        argument_spec=dict(
            data=dict(default=None),
            path=dict(default=None, type=str),
            file=dict(default=None, type=str),
        )
    )
