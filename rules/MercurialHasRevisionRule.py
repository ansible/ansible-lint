import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class MercurialHasRevisionRule(AnsibleLintRule):
    id = 'ANSIBLE0005'
    shortdesc = 'Mercurial checkouts must contain explicit revision'
    description = 'All version control checkouts must point to ' + \
                  'an explicit commit or tag, not just "latest"'

    tags = {'repeatability'}


    def _hg_match(self, line):
        (module, args) = ansiblelint.utils.tokenize(line)
        return (module == 'hg' and args.get('revision', 'default') == 'default')


    def match(self,playbook):
        return ansiblelint.utils.matchlines(playbook, self._hg_match)
