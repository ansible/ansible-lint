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

from typing import TYPE_CHECKING, Any, Dict, Union

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from typing import Optional

    from ansiblelint.file_utils import Lintable


class CommandHasChangesCheckRule(AnsibleLintRule):
    id = 'no-changed-when'
    shortdesc = 'Commands should not change things if nothing needs doing'
    description = (
        'Commands should either read information (and thus set '
        '``changed_when``) or not do something if it has already been '
        'done (using creates/removes) or only do it if another '
        'check has a particular result (``when``)'
    )
    severity = 'HIGH'
    tags = ['command-shell', 'idempotency']
    version_added = 'historic'

    _commands = ['command', 'shell', 'raw']

    def matchtask(
        self, task: Dict[str, Any], file: 'Optional[Lintable]' = None
    ) -> Union[bool, str]:
        if task["__ansible_action_type__"] == 'task':
            if task["action"]["__ansible_module__"] in self._commands:
                return (
                    'changed_when' not in task
                    and 'when' not in task
                    and 'creates' not in task['action']
                    and 'removes' not in task['action']
                    and not ('async' in task and task.get('poll') == 0)
                )
        return False
