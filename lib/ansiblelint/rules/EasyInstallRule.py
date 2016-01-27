import ansiblelint.utils
from ansiblelint import AnsibleLintRule


class EasyInstallRule(AnsibleLintRule):
    id = 'ANSIBLE1002'
    shortdesc = 'Using easy_install instead of yum'
    description = 'easy_install is not a recommended tool for installing ' + \
                  'to production machines. Switch this task to use yum.'
    tags = ['repeatability']

    def matchtask(self, file, task):
        return (task['action']['module'] == 'easy_install')
