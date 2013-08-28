import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class GitHasVersionRule(AnsibleLintRule):
    id = 'ANSIBLE0004'
    shortdesc = 'Checkouts must contain explicit version'
    description = 'All version control checkouts must point to ' + \
                  'an explicit commit or tag, not just "latest"'
    tags = {'repeatability'}


    def match(self, line):
        (module, args, kwargs) = ansiblelint.utils.tokenize(line)
        return (module == 'git' and kwargs.get('version', 'HEAD') == 'HEAD')
