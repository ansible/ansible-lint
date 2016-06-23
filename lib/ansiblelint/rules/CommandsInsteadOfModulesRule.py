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

from ansiblelint import AnsibleLintRule
try:
    from ansible.utils.boolean import boolean
except ImportError:
    from ansible.utils import boolean


class CommandsInsteadOfModulesRule(AnsibleLintRule):
    id = 'ANSIBLE0006'
    shortdesc = 'Using command rather than module'
    description = 'Executing a command when there is an Ansible module ' + \
                  'is generally a bad idea'
    tags = ['resources']

    _commands = ['command', 'shell']
    _modules = {'git': 'git', 'hg': 'hg', 'curl': 'get_url or uri', 'wget': 'get_url or uri',
                'svn': 'subversion', 'service': 'service', 'mount': 'mount',
                'rpm': 'yum or rpm_key', 'yum': 'yum', 'apt-get': 'apt-get',
                'unzip': 'unarchive', 'tar': 'unarchive', 'chkconfig': 'service',
                'rsync': 'synchronize'}

    def matchtask(self, file, task):
        if task["action"]["__ansible_module__"] in self._commands and \
                task["action"]["__ansible_arguments__"]:
            executable = os.path.basename(task["action"]["__ansible_arguments__"][0])
            if executable in self._modules and \
                    boolean(task['action'].get('warn', True)):
                message = "{0} used in place of {1} module"
                return message.format(executable, self._modules[executable])
