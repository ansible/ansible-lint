import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class GitHasVersionRule(AnsibleLintRule):
    id = 'ANSIBLE0004'
    shortdesc = 'Checkouts must contain explicit version'
    description = 'All version control checkouts must point to ' + \
                  'an explicit commit or tag, not just "latest"'
    tags = ['repeatability']


    def matchtask(self, file, task):
        return (task['action']['module'] == 'git' and task['action'].get('version', 'HEAD') == 'HEAD')
