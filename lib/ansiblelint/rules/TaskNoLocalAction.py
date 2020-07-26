# Copyright (c) 2016, Tsukinowa Inc. <info@tsukinowa.jp>
# Copyright (c) 2018, Ansible Project
from typing import TYPE_CHECKING, List, Optional

from ansiblelint.errors import MatchError
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import TargetFile


class TaskNoLocalAction(AnsibleLintRule):
    id = '504'
    shortdesc = "Do not use 'local_action', use 'delegate_to: localhost'"
    description = 'Do not use ``local_action``, use ``delegate_to: localhost``'
    severity = 'MEDIUM'
    tags = ['task']
    version_added = 'v4.0.0'

    def match(self, file: "TargetFile", line: str, line_no: Optional[int]) -> List[MatchError]:
        result = []
        if 'local_action' in line:
            result.append(MatchError(rule=self.__class__))
        return result
