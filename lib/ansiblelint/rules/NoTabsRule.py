# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project

from ansiblelint import AnsibleLintRule


class NoTabsRule(AnsibleLintRule):
    id = '203'
    shortdesc = 'Most files should not contain tabs'
    description = 'Tabs can cause unexpected display issues. Use spaces'
    tags = ['formatting']

    def match(self, file, line):
        return '\t' in line
