#!/usr/bin/python
"""A module."""

from ansible.module_utils.basic import AnsibleModule


def main() -> None:
    """Execute module."""
    module = AnsibleModule(dict())
    module.exit_json(msg="Hello 2!")


if __name__ == '__main__':
    main()
