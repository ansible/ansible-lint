"""Example implementation of a rule requiring tasks to have tags set."""
from ansiblelint.rules import AnsibleLintRule


class TaskHasTag(AnsibleLintRule):
    """Tasks must have tag."""

    id = 'EXAMPLE001'
    shortdesc = 'Tasks must have tag'
    description = 'Tasks must have tag'
    tags = ['productivity', 'tags']

    def matchtask(self, file, task):
        """Task matching method."""
        # The meta files don't have tags
        if file['type'] in ["meta", "playbooks"]:
            return False

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
