import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class TrailingWhitespaceRule(AnsibleLintRule):
    id = 'ANSIBLE0002'
    shortdesc = 'Trailing whitespace'
    description = 'There should not be any trailing whitespace'
    tags = {'formatting'}


    def match(self,playbook):
        return ansiblelint.utils.matchlines(playbook, 
                lambda x : x.rstrip() != x)
