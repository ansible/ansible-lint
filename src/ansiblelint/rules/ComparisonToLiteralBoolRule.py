# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018-2021, Ansible Project

import re
from typing import TYPE_CHECKING, Any, Dict, Union

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.utils import nested_items

if TYPE_CHECKING:
    from typing import Optional

    from ansiblelint.file_utils import Lintable


class ComparisonToLiteralBoolRule(AnsibleLintRule):
    id = 'literal-compare'
    shortdesc = "Don't compare to literal True/False"
    description = (
        'Use ``when: var`` rather than ``when: var == True`` '
        '(or conversely ``when: not var``)'
    )
    severity = 'HIGH'
    tags = ['idiom']
    version_added = 'v4.0.0'

    literal_bool_compare = re.compile("[=!]= ?(True|true|False|false)")

    def matchtask(
        self, task: Dict[str, Any], file: 'Optional[Lintable]' = None
    ) -> Union[bool, str]:
        for k, v, _ in nested_items(task):
            if k == 'when':
                if isinstance(v, str):
                    if self.literal_bool_compare.search(v):
                        return True
                elif isinstance(v, bool):
                    pass
                else:
                    for item in v:
                        if isinstance(item, str) and self.literal_bool_compare.search(
                            item
                        ):
                            return True

        return False
