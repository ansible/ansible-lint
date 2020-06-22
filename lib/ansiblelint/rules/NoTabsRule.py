# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project

from ansiblelint.rules import AnsibleLintRule


class NoTabsRule(AnsibleLintRule):
    id = '203'
    shortdesc = 'Most files should not contain tabs'
    description = 'Tabs can cause unexpected display issues, use spaces'
    severity = 'LOW'
    tags = ['formatting']
    version_added = 'v4.0.0'

    def match(self, file, line):
        return '\t' in line
