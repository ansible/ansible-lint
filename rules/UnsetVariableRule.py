import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class UnsetVariableRule(AnsibleLintRule):
    ID = 'ANSIBLE0002'
    DESCRIPTION = 'Lines containing {{ after templating ' + \
                  'suggest unmatched template variables'
    TAGS = ['templating']

    def __init__(self):
        super(self.__class__, self).__init__(id=self.ID, 
                                           description=self.DESCRIPTION,
                                           tags=self.TAGS)

    def postmatch(self,playbook):
        return ansiblelint.utils.matchlines(playbook, lambda x : "{{" in x)
