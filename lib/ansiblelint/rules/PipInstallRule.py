import ansiblelint.utils
from ansiblelint import AnsibleLintRule


class PipInstallRule(AnsibleLintRule):
    id = 'ANSIBLE1001'
    shortdesc = 'Using pip instead of yum'
    description = 'pip is not a recommended tool for installing ' + \
                  'to production machines. Switch this task to use yum.'
    tags = ['repeatability']

    def matchtask(self, file, task):
        return (task['action']['module'] == 'pip')
