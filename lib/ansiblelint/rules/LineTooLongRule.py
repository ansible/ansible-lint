# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project
from typing import TYPE_CHECKING, List, Optional

from ansiblelint.errors import MatchError
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import TargetFile


class LineTooLongRule(AnsibleLintRule):
    id = '204'
    shortdesc = 'Lines should be no longer than 160 chars'
    description = (
        'Long lines make code harder to read and '
        'code review more difficult'
    )
    severity = 'VERY_LOW'
    tags = ['formatting']
    version_added = 'v4.0.0'

    def match(self, file: "TargetFile", line: str, line_no: Optional[int]) -> List["MatchError"]:
        if len(line) > 160:
            return [MatchError(
                filename=file['path'],
                details=line,
                rule=self.__class__)]
        return []
