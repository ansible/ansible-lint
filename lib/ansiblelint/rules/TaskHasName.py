import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class TaskHasName(AnsibleLintRule):
    id = 'ANSIBLE1004'
    shortdesc = 'Tasks must have name'
    description = 'Tasks must have name'
    tags = ['productivity']


    def matchtask(self, file, task):
        # If the task include another task or make the playbook fail
        # Don't force to have a tag
        if not set(task.keys()).isdisjoint(['include','fail']):
            return False

        # Task should have tags
        if not task.has_key('name'):
              return True

        return False
