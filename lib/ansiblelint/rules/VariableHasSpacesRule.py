# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project

import re

from ansiblelint.rules import AnsibleLintRule


class VariableHasSpacesRule(AnsibleLintRule):
    id = '206'
    shortdesc = 'Variables should have spaces before and after: {{ var_name }}'
    description = 'Variables should have spaces before and after: ``{{ var_name }}``'
    severity = 'LOW'
    tags = ['formatting']
    version_added = 'v4.0.0'

    variable_syntax = re.compile(r"{{.*}}")
    bracket_regex = re.compile(r"{{[^{' -]|[^ '}-]}}")

    def match(self, file, line):
        if not self.variable_syntax.search(line):
            return
        line_exclude_json = re.sub(r"[^{]{'\w+': ?[^{]{.*?}}", "", line)
        return self.bracket_regex.search(line_exclude_json)
