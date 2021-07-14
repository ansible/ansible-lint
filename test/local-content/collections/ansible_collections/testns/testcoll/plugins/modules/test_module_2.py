#!/usr/bin/python

# Switching the pre-commit repo from the deprecated pylint-mirrors to pylint caused this pylint issue to surface.
# The disable can be removed if it is a false positive which will be fixed in upstream pylint or the cyclic-import is fixed such that pylint no longer complains
# pylint: disable=cyclic-import

"""A module."""

from ansible.module_utils.basic import AnsibleModule


def main() -> None:
    """Execute module."""
    module = AnsibleModule(dict())
    module.exit_json(msg="Hello 2!")


if __name__ == '__main__':
    main()
