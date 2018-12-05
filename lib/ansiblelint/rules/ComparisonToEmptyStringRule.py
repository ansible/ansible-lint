# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project

from ansiblelint import AnsibleLintRule
import re


class ComparisonToEmptyStringRule(AnsibleLintRule):
    id = '602'
    shortdesc = "Don't compare to empty string"
    description = (
        'Use ``when: var`` rather than ``when: var != ""`` (or '
        'conversely ``when: not var`` rather than ``when: var == ""``)'
    )
    severity = 'HIGH'
    tags = ['idiom']
    version_added = 'v4.0.0'

    empty_string_compare = re.compile("[=!]= ?[\"'][\"']")

    def match(self, file, line):
        return self.empty_string_compare.search(line)
