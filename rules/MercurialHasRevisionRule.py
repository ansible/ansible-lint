import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class MercurialHasRevisionRule(AnsibleLintRule):
    id = 'ANSIBLE0005'
    shortdesc = 'Mercurial checkouts must contain explicit revision'
    description = 'All version control checkouts must point to ' + \
                  'an explicit commit or tag, not just "latest"'

    tags = ['repeatability']


    def match(self, line):
        (module, args, kwargs) = ansiblelint.utils.tokenize(line)
        return (module == 'hg' and kwargs.get('revision', 'default') == 'default')
