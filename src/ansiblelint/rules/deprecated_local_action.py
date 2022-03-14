"""Implementation for deprecated-local-action rule."""
# Copyright (c) 2016, Tsukinowa Inc. <info@tsukinowa.jp>
# Copyright (c) 2018, Ansible Project
from ansiblelint.rules import AnsibleLintRule


class TaskNoLocalAction(AnsibleLintRule):
    """Do not use 'local_action', use 'delegate_to: localhost'."""

    id = "deprecated-local-action"
    description = "Do not use ``local_action``, use ``delegate_to: localhost``"
    severity = "MEDIUM"
    tags = ["deprecations"]
    version_added = "v4.0.0"

    def match(self, line: str) -> bool:
        if "local_action" in line:
            return True
        return False
