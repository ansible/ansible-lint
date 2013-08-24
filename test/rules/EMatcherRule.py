import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class EMatcherRule(AnsibleLintRule):
    ID = 'TEST0001'
    DESCRIPTION = 'This is a test rule that looks for lines ' + \
                  'containing the letter e'
    SHORTDESC = 'The letter "e" is present'
    TAGS = ['fake', 'dummy', 'test1']

    def __init__(self):
        super(self.__class__, self).__init__(id=self.ID, 
                                             shortdesc=self.SHORTDESC,
                                             description=self.DESCRIPTION,
                                             tags=self.TAGS)

    def match(self,playbook):
        return ansiblelint.utils.matchlines(playbook, lambda x : "e" in x)
