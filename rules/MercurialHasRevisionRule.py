import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class MercurialHasRevisionRule(AnsibleLintRule):
    ID = 'ANSIBLE0005'
    SHORTDESC = 'Mercurial checkouts must contain explicit revision'
    DESCRIPTION = 'All version control checkouts must point to ' + \
                  'an explicit commit or tag, not just "latest"'
    TAGS = ['repeatability']

    def __init__(self):
        super(self.__class__, self).__init__(id=self.ID, 
                                             shortdesc=self.SHORTDESC,
                                             description=self.DESCRIPTION,
                                             tags=self.TAGS)

    def _hg_match(self, line):
        (module, args) = ansiblelint.utils.tokenize(line)
        return (module == 'hg' and args.get('revision', 'default') == 'default')


    def match(self,playbook):
        return ansiblelint.utils.matchlines(playbook, self._hg_match)
