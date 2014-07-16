import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class MercurialHasRevisionRule(AnsibleLintRule):
    id = 'ANSIBLE0005'
    shortdesc = 'Mercurial checkouts must contain explicit revision'
    description = 'All version control checkouts must point to ' + \
                  'an explicit commit or tag, not just "latest"'

    tags = ['repeatability']


    def matchtask(self, file, task):
        return task['action']['module'] == 'hg' and task['action'].get('revision', 'default') == 'default'
