"""Sample custom ansible module named fake_module.

This is used to test ability to detect and use custom modules.
"""
from ansible.module_utils.basic import AnsibleModule


def main() -> None:
    """Return the module instance."""
    return AnsibleModule(
        argument_spec={
            "data": {"default": None},
            "path": {"default": None},
            "file": {"default": None},
        }
    )
