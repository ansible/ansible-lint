from ansiblelint import AnsibleLintRule

class DeprecatedTemplateBracketsRule(AnsibleLintRule):
    id = 'ANSIBLE0001'
    shortdesc = 'Old style (${var}) brackets'
    description = 'Checks for old style ${var} ' + \
                  'rather than {{var}}'

    tags = ['deprecation']

    def match(self, file, line):
        return "${" in line
