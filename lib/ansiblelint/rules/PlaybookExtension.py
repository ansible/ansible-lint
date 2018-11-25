# Copyright (c) 2016, Tsukinowa Inc. <info@tsukinowa.jp>
# Copyright (c) 2018, Ansible Project

from ansiblelint import AnsibleLintRule

import os


class PlaybookExtension(AnsibleLintRule):
    id = '205'
    shortdesc = 'Playbooks should have the ".yml" extension'
    description = ''
    tags = ['formatting']
    done = []  # already noticed path list

    def match(self, file, text):
        if file['type'] != 'playbook':
            return False

        path = file['path']
        ext = os.path.splitext(path)
        if ext[1] not in ['.yml', '.yaml'] and path not in self.done:
            self.done.append(path)
            return True
        return False
