import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class UnsetVariableMatcherRule(AnsibleLintRule):
    def __init__(self):
        super(UnsetVariableMatcherRule, self).__init__()

        self.id = 'TEST0002'
        self.shortdesc = 'Line contains untemplated variable'
        self.description = 'This is a test rule that looks for lines ' + \
                           'post templating that still contain {{'
        self.tags = {'fake', 'dummy', 'test2'}

    def match(self,filename,line):
        return "{{" in line
