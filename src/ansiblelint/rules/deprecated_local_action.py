"""Implementation for deprecated-local-action rule."""
# Copyright (c) 2016, Tsukinowa Inc. <info@tsukinowa.jp>
# Copyright (c) 2018, Ansible Project

import sys

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


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:

    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.testing import RunFromText

    TASK_LOCAL_ACTION = """
    - name: task example
      local_action:
        module: boto3_facts
    """

    def test_local_action() -> None:
        """Positive test deprecated_local_action."""
        collection = RulesCollection()
        collection.register(TaskNoLocalAction())
        runner = RunFromText(collection)
        results = runner.run_role_tasks_main(TASK_LOCAL_ACTION)
        assert len(results) == 1
