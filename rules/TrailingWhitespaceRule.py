from ansiblelint import AnsibleLintRule

class TrailingWhitespaceRule(AnsibleLintRule):
    id = 'ANSIBLE0002'
    shortdesc = 'Trailing whitespace'
    description = 'There should not be any trailing whitespace'
    tags = ['formatting']


    def match(self, line):
        return line.rstrip() != line
