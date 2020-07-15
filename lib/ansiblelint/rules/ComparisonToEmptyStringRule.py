# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project

import re

from ansiblelint.rules import AnsibleLintRule


class ComparisonToEmptyStringRule(AnsibleLintRule):
    id = '602'
    shortdesc = "Don't compare to empty string"
    description = (
        'Use ``when: var|length > 0`` rather than ``when: var != ""`` (or '
        'conversely ``when: var|length == 0`` rather than ``when: var == ""``)'
    )
    severity = 'HIGH'
    tags = ['idiom']
    version_added = 'v4.0.0'

    empty_string_compare = re.compile("[=!]= ?(\"{2}|'{2})")

    def match(self, file, line):
        return self.empty_string_compare.search(line)
