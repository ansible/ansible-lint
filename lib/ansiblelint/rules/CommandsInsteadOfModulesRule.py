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


class CommandsInsteadOfModulesRule(AnsibleLintRule):
    _commands = ['command', 'shell']
    _modules = {'git': 'git', 'hg': 'hg', 'curl': 'get_url', 'wget': 'get_url',
                'svn': 'subversion', 'service': 'service', 'mount': 'mount',
                'rpm': 'yum', 'yum': 'yum', 'apt-get': 'apt-get',
                'unzip': 'unarchive', 'tar': 'unarchive'}

    def __init__(self):
        super(CommandsInsteadOfModulesRule, self).__init__()

        self.id = 'ANSIBLE0006'
        self.shortdesc = 'Using command rather than module'
        self.description = 'Executing a command when there is an Ansible module ' + \
                           'is generally a bad idea'
        self.tags = ['resources']

    def matchtask(self, ansiblefile, task):
        del ansiblefile

        if task["action"]["module"] in self._commands:
            executable = os.path.basename(task["action"]["module_arguments"][0])
            if executable in self._modules:
                message = "{0} used in place of {1} module"
                return message.format(executable, self._modules[executable])
