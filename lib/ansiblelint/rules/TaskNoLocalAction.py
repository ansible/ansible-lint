# Copyright (c) 2016, Tsukinowa Inc. <info@tsukinowa.jp>
# Copyright (c) 2018, Ansible Project

from ansiblelint.rules import AnsibleLintRule


class TaskNoLocalAction(AnsibleLintRule):
    id = '504'
    shortdesc = "Do not use 'local_action', use 'delegate_to: localhost'"
    description = 'Do not use ``local_action``, use ``delegate_to: localhost``'
    severity = 'MEDIUM'
    tags = ['task']
    version_added = 'v4.0.0'

    def match(self, file, text):
        if 'local_action' in text:
            return True
        return False
