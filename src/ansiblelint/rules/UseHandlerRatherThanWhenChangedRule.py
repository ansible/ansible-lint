# Copyright (c) 2016 Will Thames <will@thames.id.au>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import sys
from typing import Any, Dict, Union

from ansiblelint.rules import AnsibleLintRule


def _changed_in_when(item: str) -> bool:
    if not isinstance(item, str):
        return False
    return any(
        changed in item
        for changed in [
            '.changed',
            '|changed',
            '["changed"]',
            "['changed']",
            "is changed",
        ]
    )


class UseHandlerRatherThanWhenChangedRule(AnsibleLintRule):
    id = 'no-handler'
    shortdesc = 'Tasks that run when changed should likely be handlers'
    description = (
        'If a task has a ``when: result.changed`` setting, it is effectively '
        'acting as a handler. You could use notify and move that task to '
        'handlers.'
    )
    link = "https://docs.ansible.com/ansible/latest/user_guide/playbooks_handlers.html"
    severity = 'MEDIUM'
    tags = ['idiom']
    version_added = 'historic'

    def matchtask(self, task: Dict[str, Any]) -> Union[bool, str]:
        if task["__ansible_action_type__"] != 'task':
            return False

        when = task.get('when')

        if isinstance(when, list):
            for item in when:
                return _changed_in_when(item)
        if isinstance(when, str):
            return _changed_in_when(when)
        return False


if 'pytest' in sys.modules:

    from ansiblelint.file_utils import Lintable
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    def test_rule_no_handler() -> None:
        """Verify rule."""
        collection = RulesCollection()
        collection.register(UseHandlerRatherThanWhenChangedRule())

        lintable = Lintable('examples/playbooks/rule-no-handler.yml')
        results = Runner(lintable, rules=collection).run()

        assert len(results) == 3
        assert results[0].filename == 'examples/playbooks/roles/a-role/tasks/main.yml'
        assert results[0].linenumber == 3
        assert results[1].filename == 'examples/playbooks/rule-no-handler.yml'
        assert results[1].linenumber == 14
        assert results[2].filename == 'examples/playbooks/rule-no-handler.yml'
        assert results[2].linenumber == 18
