import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class MismatchedBracketRule(AnsibleLintRule):
    id = 'ANSIBLE0003'
    shortdesc='Mismatched { and }'
    description = 'If lines contain more { than } or vice ' + \
                  'versa then templating can fail nastily'
    tags = {'templating'}


    def match(self,playbook):
        return ansiblelint.utils.matchlines(playbook, 
                lambda x : x.count("{") != x.count("}"))
