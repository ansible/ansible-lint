# Copyright (c) 2016, Tsukinowa Inc. <info@tsukinowa.jp>
# Copyright (c) 2018, Ansible Project

from ansiblelint import AnsibleLintRule


class ShellAltPatch(AnsibleLintRule):
    id = '306'
    shortdesc = 'Use patch module'
    description = ''
    tags = ['command-shell']

    def matchtask(self, file, task):
        if task['action']['__ansible_module__'] not in ['shell', 'command']:
            return False
        if 'patch' in task['action']['__ansible_arguments__']:
            return True
        return False
