import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class DeprecatedTemplateBracketsRule(AnsibleLintRule):
    ID = 'ANSIBLE0001'
    SHORTDESC = 'Old style (${var}) brackets'
    DESCRIPTION = 'Checks for old style ${var} ' + \
                  'rather than {{var}}'

    TAGS = {'deprecation'}

    def __init__(self):
        super(self.__class__, self).__init__(id=self.ID, 
                                             shortdesc=self.SHORTDESC,
                                             description=self.DESCRIPTION,
                                             tags=self.TAGS)

    def match(self,playbook):
        return ansiblelint.utils.matchlines(playbook, lambda x : "${" in x)
