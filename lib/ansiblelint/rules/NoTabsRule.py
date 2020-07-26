# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project
from typing import List, Optional

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import TargetFile
from ansiblelint.rules import AnsibleLintRule


class NoTabsRule(AnsibleLintRule):
    id = '203'
    shortdesc = 'Most files should not contain tabs'
    description = 'Tabs can cause unexpected display issues, use spaces'
    severity = 'LOW'
    tags = ['formatting']
    version_added = 'v4.0.0'

    def match(self, file: TargetFile, line: str, line_no: Optional[int]) -> List[MatchError]:
        result = []
        if '\t' in line:
            result.append(MatchError(rule=self.__class__))
        return result
