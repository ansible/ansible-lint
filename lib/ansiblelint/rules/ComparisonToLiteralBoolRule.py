# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project

from ansiblelint.rules import AnsibleLintRule
import re


class ComparisonToLiteralBoolRule(AnsibleLintRule):
    id = '601'
    shortdesc = "Don't compare to literal boolean."
    description = (
        'Use ``when: var`` instead of ``when: var == True``, '
        'or ``when: not var`` for negative checks.'
    )
    severity = 'HIGH'
    tags = ['idiom']
    version_added = 'v4.0.0'

    literal_bool_compare = re.compile("[=!]= ?(True|true|False|false)")

    def match(self, file, line):
        return self.literal_bool_compare.search(line)
