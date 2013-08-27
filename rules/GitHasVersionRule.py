import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class GitHasVersionRule(AnsibleLintRule):
    id = 'ANSIBLE0004'
    shortdesc = 'Checkouts must contain explicit version'
    description = 'All version control checkouts must point to ' + \
                  'an explicit commit or tag, not just "latest"'
    tags = {'repeatability'}


    def _git_match(self, line):
        tokens = ansiblelint.utils.tokenize(line)
        if tokens[0] == 'git':
            for arg in tokens[1:]:
                if isinstance(arg, dict) and arg.has_key('version') and arg.get('version') != 'HEAD':
                    return False
            return True
        return False


    def match(self,playbook):
        return ansiblelint.utils.matchlines(playbook, self._git_match)
