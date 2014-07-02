import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class TaskHasTag(AnsibleLintRule):
    id = 'ANSIBLE0008'
    shortdesc = 'Tasks must have tag'
    description = 'Tasks must have tag'
    tags = ['productivity']


    def matchblock(self, file, block):
        # The meta files don't have tags
        if file['type'] in ["meta", "playbooks"]:
            return False

        if isinstance(block, basestring):
            return False

        # If the task include another task or make the playbook fail
        # Don't force to have a tag
        if not set(block.keys()).isdisjoint(['include','fail']):
            return False

        # Task should have tags
        if not block.has_key('tags'):
              return True

        return False

