# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project

from ansiblelint import AnsibleLintRule
import re


class VariableHasSpacesRule(AnsibleLintRule):
    id = '206'
    shortdesc = 'Variables should have spaces before and after: {{ var_name }}'
    description = 'Variables should have spaces before and after: ``{{ var_name }}``'
    severity = 'LOW'
    tags = ['formatting']
    version_added = 'v4.0.0'

    bracket_regex = re.compile("{{[^{ ]|[^ }]}}")

    def match(self, file, line):
        return self.bracket_regex.search(line)
