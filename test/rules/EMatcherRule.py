import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class EMatcherRule(AnsibleLintRule):
    id = 'TEST0001'
    description = 'This is a test rule that looks for lines ' + \
                  'containing the letter e'
    shortdesc = 'The letter "e" is present'
    tags = {'fake', 'dummy', 'test1'}

    def match(self, file, line):
        return "e" in line
