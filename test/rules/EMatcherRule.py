import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class EMatcherRule(AnsibleLintRule):
    def __init__(self):
        super(EMatcherRule, self).__init__()

        self.id = 'TEST0001'
        self.description = 'This is a test rule that looks for lines ' + \
                           'containing the letter e'
        self.shortdesc = 'The letter "e" is present'
        self.tags = {'fake', 'dummy', 'test1'}

    def match(self, filename, line):
        return "e" in line
