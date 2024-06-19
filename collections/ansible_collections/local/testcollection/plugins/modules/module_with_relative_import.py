"""module_with_relative_import module."""

from ansible.module_utils.basic import AnsibleModule

# pylint: disable=E0402
from ..module_utils import MY_STRING  # noqa: TID252 # type: ignore[import-untyped]

DOCUMENTATION = r"""
options:
  name:
    required: True
"""


def main() -> AnsibleModule:
    """The main function."""
    return AnsibleModule(
        argument_spec={
            "name": {"required": True, "aliases": [MY_STRING]},
        },
    )


if __name__ == "__main__":
    main()
