from ansiblelint.rules import AnsibleLintRule


class EMatcherRule(AnsibleLintRule):
    id = 'TEST0001'
    description = (
        'This is a test custom rule that looks for lines ' + 'containing BANNED string'
    )
    shortdesc = 'BANNED string found'
    tags = ['fake', 'dummy', 'test1']

    def match(self, line: str) -> bool:
        return "BANNED" in line
