import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class GitHasVersionRule(AnsibleLintRule):
    id = 'ANSIBLE0004'
    shortdesc = 'Checkouts must contain explicit version'
    description = 'All version control checkouts must point to ' + \
                  'an explicit commit or tag, not just "latest"'
    tags = {'repeatability'}


    def _git_match(self, line):
        (module, args) = ansiblelint.utils.tokenize(line)
        return (module == 'git' and args.get('version', 'HEAD') == 'HEAD')


    def match(self,playbook):
        return ansiblelint.utils.matchlines(playbook, self._git_match)
