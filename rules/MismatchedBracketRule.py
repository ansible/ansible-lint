import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class MismatchedBracketRule(AnsibleLintRule):
    ID = 'ANSIBLE0003'
    DESCRIPTION = 'If lines contain more { than } or vice ' + \
                  'versa then templating can fail nastily'
    TAGS = ['templating']

    def __init__(self):
        super(self.__class__, self).__init__(id=self.ID, 
                                           description=self.DESCRIPTION,
                                           tags=self.TAGS)

    def prematch(self,playbook):
        return ansiblelint.utils.matchlines(playbook, 
                lambda x : x.count("{") != x.count("}"))
