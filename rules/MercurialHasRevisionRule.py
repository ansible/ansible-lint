import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class MercurialHasRevisionRule(AnsibleLintRule):
    id = 'ANSIBLE0005'
    shortdesc = 'Mercurial checkouts must contain explicit revision'
    description = 'All version control checkouts must point to ' + \
                  'an explicit commit or tag, not just "latest"'

    tags = {'repeatability'}


    def _hg_match(self, line):
        tokens = ansiblelint.utils.tokenize(line)
        if tokens[0] == 'hg':
            for arg in tokens[1:]:
                if isinstance(arg, dict) and arg.has_key('revision') and arg.get('revision') != 'default':
                    return False
            return True
        return False


    def match(self,playbook):
        return ansiblelint.utils.matchlines(playbook, self._hg_match)
