import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class UnsetVariableMatcherRule(AnsibleLintRule):
    ID = 'TEST0002'
    SHORTDESC = 'Line contains untemplated variable'
    DESCRIPTION = 'This is a test rule that looks for lines ' + \
                  'post templating that still contain {{'
    TAGS = ['fake', 'dummy', 'test2']

    def __init__(self):
        super(self.__class__, self).__init__(id=self.ID, 
                                             shortdesc=self.SHORTDESC,
                                             description=self.DESCRIPTION,
                                             tags=self.TAGS)

    def match(self,playbook):
        return ansiblelint.utils.matchlines(playbook, lambda x : "{{" in x)
