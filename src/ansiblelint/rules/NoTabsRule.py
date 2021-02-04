# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project
from typing import Any, Dict, Union

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.utils import nested_items


class NoTabsRule(AnsibleLintRule):
    id = 'no-tabs'
    shortdesc = 'Most files should not contain tabs'
    description = 'Tabs can cause unexpected display issues, use spaces'
    severity = 'LOW'
    tags = ['formatting']
    version_added = 'v4.0.0'

    def matchtask(self, task: Dict[str, Any]) -> Union[bool, str]:
        for k, v in nested_items(task):
            if isinstance(k, str) and '\t' in k:
                return True
            if isinstance(v, str) and '\t' in v:
                return True
        return False
