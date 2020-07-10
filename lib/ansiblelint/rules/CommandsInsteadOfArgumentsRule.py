# Copyright (c) 2013-2014 Will Thames <will@thames.id.au>
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

import os

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.utils import get_first_cmd_arg

try:
    from ansible.module_utils.parsing.convert_bool import boolean
except ImportError:
    try:
        from ansible.utils.boolean import boolean
    except ImportError:
        try:
            from ansible.utils import boolean
        except ImportError:
            from ansible import constants
            boolean = constants.mk_boolean


class CommandsInsteadOfArgumentsRule(AnsibleLintRule):
    id = '302'
    shortdesc = 'Using command rather than an argument to e.g. file'
    description = (
        'Executing a command when there are arguments to modules '
        'is generally a bad idea'
    )
    severity = 'VERY_HIGH'
    tags = ['command-shell', 'resources', 'ANSIBLE0007']
    version_added = 'historic'

    _commands = ['command', 'shell', 'raw']
    _arguments = {'chown': 'owner', 'chmod': 'mode', 'chgrp': 'group',
                  'ln': 'state=link', 'mkdir': 'state=directory',
                  'rmdir': 'state=absent', 'rm': 'state=absent'}

    def matchtask(self, file, task):
        if task["action"]["__ansible_module__"] in self._commands:
            first_cmd_arg = get_first_cmd_arg(task)
            if not first_cmd_arg:
                return

            executable = os.path.basename(first_cmd_arg)
            if executable in self._arguments and \
                    boolean(task['action'].get('warn', True)):
                message = "{0} used in place of argument {1} to file module"
                return message.format(executable, self._arguments[executable])
