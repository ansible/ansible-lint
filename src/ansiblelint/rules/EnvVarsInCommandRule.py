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
from ansiblelint.utils import FILENAME_KEY, LINE_NUMBER_KEY, get_first_cmd_arg

if TYPE_CHECKING:
    from typing import Optional

    from ansiblelint.file_utils import Lintable


class EnvVarsInCommandRule(AnsibleLintRule):
    id = 'inline-env-var'
    shortdesc = "Command module does not accept setting environment variables inline"
    description = (
        'Use ``environment:`` to set environment variables '
        'or use ``shell`` module which accepts both'
    )
    severity = 'VERY_HIGH'
    tags = ['command-shell', 'idiom']
    version_added = 'historic'

    expected_args = [
        'chdir',
        'creates',
        'executable',
        'removes',
        'stdin',
        'warn',
        'stdin_add_newline',
        'strip_empty_ends',
        'cmd',
        '__ansible_module__',
        '__ansible_module_original__',
        '__ansible_arguments__',
        LINE_NUMBER_KEY,
        FILENAME_KEY,
    ]

    def matchtask(
        self, task: Dict[str, Any], file: 'Optional[Lintable]' = None
    ) -> Union[bool, str]:
        if task["action"]["__ansible_module__"] in ['command']:
            first_cmd_arg = get_first_cmd_arg(task)
            if not first_cmd_arg:
                return False

            return any(
                [arg not in self.expected_args for arg in task['action']]
                + ["=" in first_cmd_arg]
            )
        return False
