import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class TrailingWhitespaceRule(AnsibleLintRule):
    ID = 'ANSIBLE0002'
    SHORTDESC = 'Trailing whitespace'
    DESCRIPTION = 'There should not be any trailing whitespace'
    TAGS = {'formatting'}

    def __init__(self):
        super(self.__class__, self).__init__(id=self.ID, 
                                             shortdesc=self.SHORTDESC,
                                             description=self.DESCRIPTION,
                                             tags=self.TAGS)

    def match(self,playbook):
        return ansiblelint.utils.matchlines(playbook, 
                lambda x : x.rstrip() != x)
