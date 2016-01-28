from ansiblelint import AnsibleLintRule


class SnakeCaseRule(AnsibleLintRule):
    id = 'SNAKE001'
    description = 'This is a test rule with a snake_case filename'
    shortdesc = 'snake_case'
    tags = {'fake', 'dummy', 'test1'}

    def match(self, filename, line):
        return True
