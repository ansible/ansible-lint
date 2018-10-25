# Copyright (c) 2016, Tsukinowa Inc. <info@tsukinowa.jp>
# Copyright (c) 2018, Ansible Project

from ansiblelint import AnsibleLintRule

import re


class TaskVariableHasSpace(AnsibleLintRule):
    id = '205'
    shortdesc = 'Variables should be enclosed by spaces "{{ foo }}"'
    description = ''
    tags = ['formatting']

    compiled = re.compile(r'{{(\w*)}}')

    def match(self, file, text):
        m = self.compiled.search(text)
        if m:
            return True
        return False
