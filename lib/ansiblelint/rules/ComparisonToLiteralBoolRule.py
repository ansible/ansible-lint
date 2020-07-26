# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project

import re
from typing import TYPE_CHECKING, List, Optional

from ansiblelint.errors import MatchError
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import TargetFile


class ComparisonToLiteralBoolRule(AnsibleLintRule):
    id = '601'
    shortdesc = "Don't compare to literal True/False"
    description = (
        'Use ``when: var`` rather than ``when: var == True`` '
        '(or conversely ``when: not var``)'
    )
    severity = 'HIGH'
    tags = ['idiom']
    version_added = 'v4.0.0'

    literal_bool_compare = re.compile("[=!]= ?(True|true|False|false)")

    def match(self, file: "TargetFile", line: str, line_no: Optional[int]) -> List["MatchError"]:
        if self.literal_bool_compare.search(line):
            return [MatchError(rule=self.__class__)]
        return []
