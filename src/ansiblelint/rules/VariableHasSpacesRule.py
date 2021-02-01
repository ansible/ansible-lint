# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project

import re
import sys
from typing import Any, Dict, Union

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.utils import nested_items


class VariableHasSpacesRule(AnsibleLintRule):
    id = '206'
    shortdesc = 'Variables should have spaces before and after: {{ var_name }}'
    description = 'Variables should have spaces before and after: ``{{ var_name }}``'
    severity = 'LOW'
    tags = ['formatting']
    version_added = 'v4.0.0'

    variable_syntax = re.compile(r"{{.*}}")
    bracket_regex = re.compile(r"{{[^{' -]|[^ '}-]}}")

    def matchtask(self, task: Dict[str, Any]) -> Union[bool, str]:
        for k, v in nested_items(task):
            if isinstance(v, str):
                line_exclude_json = re.sub(r"[^{]{'\w+': ?[^{]{.*?}}", "", v)
                if bool(self.bracket_regex.search(line_exclude_json)):
                    return True
        return False


if 'pytest' in sys.modules:

    from ansiblelint.file_utils import Lintable
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    def test_206() -> None:
        """Verify rule."""
        collection = RulesCollection()
        collection.register(VariableHasSpacesRule())

        lintable = Lintable("examples/playbooks/206.yml")
        results = Runner(
            lintable,
            rules=collection).run()

        assert len(results) == 3
