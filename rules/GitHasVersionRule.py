import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class GitHasVersionRule(AnsibleLintRule):
    ID = 'ANSIBLE0004'
    SHORTDESC = 'Checkouts must contain explicit version'
    DESCRIPTION = 'All version control checkouts must point to ' + \
                  'an explicit commit or tag, not just "latest"'
    TAGS = ['repeatability']

    def __init__(self):
        super(self.__class__, self).__init__(id=self.ID, 
                                             shortdesc=self.SHORTDESC,
                                             description=self.DESCRIPTION,
                                             tags=self.TAGS)

    def _git_match(self, line):
        (module, args) = ansiblelint.utils.tokenize(line)
        return (module == 'git' and args.get('version', 'HEAD') == 'HEAD')


    def match(self,playbook):
        return ansiblelint.utils.matchlines(playbook, self._git_match)
