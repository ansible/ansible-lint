import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class UnsetVariableMatcherRule(AnsibleLintRule):
    id = 'TEST0002'
    shortdesc = 'Line contains untemplated variable'
    description = 'This is a test rule that looks for lines ' + \
                  'post templating that still contain {{'
    tags = {'fake', 'dummy', 'test2'}

    def match(self, file, line):
        return "{{" in line
