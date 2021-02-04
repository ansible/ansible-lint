# Copyright (c) 2016, Tsukinowa Inc. <info@tsukinowa.jp>
# Copyright (c) 2018, Ansible Project

import os
from typing import List

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule


class PlaybookExtension(AnsibleLintRule):
    id = 'playbook-extension'
    shortdesc = 'Use ".yml" or ".yaml" playbook extension'
    description = 'Playbooks should have the ".yml" or ".yaml" extension'
    severity = 'MEDIUM'
    tags = ['formatting']
    done: List[str] = []
    version_added = 'v4.0.0'

    def matchyaml(self, file: Lintable) -> List[MatchError]:
        result: List[MatchError] = []
        if file.kind != 'playbook':
            return result
        path = str(file.path)
        ext = os.path.splitext(path)
        if ext[1] not in ['.yml', '.yaml'] and path not in self.done:
            self.done.append(path)
            result.append(self.create_matcherror(filename=path))
        return result
