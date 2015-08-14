from ansiblelint import AnsibleLintRule


class TaskHasTag(AnsibleLintRule):
    id = 'EXAMPLE001'
    shortdesc = 'Tasks must have tag'
    description = 'Tasks must have tag'
    tags = ['productivity', 'tags']

    def matchtask(self, file, task):
        # The meta files don't have tags
        if file['type'] in ["meta", "playbooks"]:
            return False

        if isinstance(task, basestring):
            return False

        # If the task include another task or make the playbook fail
        # Don't force to have a tag
        if not set(task.keys()).isdisjoint(['include', 'fail']):
            return False

        # Task should have tags
        if 'tags' not in task:
            return True

        return False
