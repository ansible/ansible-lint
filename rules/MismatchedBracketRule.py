from ansiblelint import AnsibleLintRule

class MismatchedBracketRule(AnsibleLintRule):
    id = 'ANSIBLE0003'
    shortdesc='Mismatched { and }'
    description = 'If lines contain more { than } or vice ' + \
                  'versa then templating can fail nastily'
    tags = ['templating']


    def match(self, line):
        return line.count("{") != line.count("}")
