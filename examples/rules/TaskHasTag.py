"""Example implementation of a rule requiring tasks to have tags set."""
from typing import Any, Dict, Union

from ansiblelint.rules import AnsibleLintRule


class TaskHasTag(AnsibleLintRule):
    """Tasks must have tag."""

    id = 'EXAMPLE001'
    shortdesc = 'Tasks must have tag'
    description = 'Tasks must have tag'
    tags = ['productivity', 'tags']

    def matchtask(self, task: Dict[str, Any]) -> Union[bool, str]:
        """Task matching method."""
        if isinstance(task, str):
            return False

        # If the task include another task or make the playbook fail
        # Don't force to have a tag
        if not set(task.keys()).isdisjoint(['include', 'fail']):
            return False

        if not set(task.keys()).isdisjoint(['include_tasks', 'fail']):
            return False

        if not set(task.keys()).isdisjoint(['import_tasks', 'fail']):
            return False

        # Task should have tags
        if 'tags' not in task:
            return True

        return False
