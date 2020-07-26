# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project

import re
from typing import TYPE_CHECKING, List, Optional

from ansiblelint.errors import MatchError
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import TargetFile


class ComparisonToEmptyStringRule(AnsibleLintRule):
    id = '602'
    shortdesc = "Don't compare to empty string"
    description = (
        'Use ``when: var|length > 0`` rather than ``when: var != ""`` (or '
        'conversely ``when: var|length == 0`` rather than ``when: var == ""``)'
    )
    severity = 'HIGH'
    tags = ['idiom']
    version_added = 'v4.0.0'

    empty_string_compare = re.compile("[=!]= ?(\"{2}|'{2})")

    def match(self, file: "TargetFile", line: str, line_no: Optional[int]) -> List["MatchError"]:
        result = []
        if self.empty_string_compare.search(line):
            result.append(MatchError(filename=file['path'], details=line, rule=self.__class__))
        return result
