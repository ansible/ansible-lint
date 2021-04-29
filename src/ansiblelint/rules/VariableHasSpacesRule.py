# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project

import re
import sys
from typing import Any, Dict, Optional, Union

from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.utils import nested_items


class VariableHasSpacesRule(AnsibleLintRule):
    id = 'var-spacing'
    base_msg = 'Variables should have spaces before and after: '
    shortdesc = base_msg + ' {{ var_name }}'
    description = 'Variables should have spaces before and after: ``{{ var_name }}``'
    severity = 'LOW'
    tags = ['formatting']
    version_added = 'v4.0.0'

    bracket_regex = re.compile(r"{{[^{\n' -]|[^ '\n}-]}}", re.MULTILINE | re.DOTALL)
    exclude_json_re = re.compile(r"[^{]{'\w+': ?[^{]{.*?}}")

    def matchtask(
        self, task: Dict[str, Any], file: Optional[Lintable] = None
    ) -> Union[bool, str]:
        for k, v, _ in nested_items(task):
            if isinstance(v, str):
                cleaned = self.exclude_json_re.sub("", v)
                if bool(self.bracket_regex.search(cleaned)):
                    return self.base_msg + v
        return False


if 'pytest' in sys.modules:

    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    def test_var_spacing() -> None:
        """Verify rule."""
        collection = RulesCollection()
        collection.register(VariableHasSpacesRule())

        lintable = Lintable("examples/playbooks/var-spacing.yml")
        results = Runner(lintable, rules=collection).run()

        assert len(results) == 3
