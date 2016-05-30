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

from ansiblelint import AnsibleLintRule
from ansiblelint.utils import LINE_NUMBER_KEY, FILENAME_KEY


class EnvVarsInCommandRule(AnsibleLintRule):
    id = 'ANSIBLE0014'
    shortdesc = "Environment variables don't work as part of command"
    description = 'Environment variables should be passed to shell or ' \
                  'command through environment argument'
    tags = ['bug']

    expected_args = ['chdir', 'creates', 'executable', 'removes', 'warn',
                     '__ansible_module__', '__ansible_arguments__',
                     LINE_NUMBER_KEY, FILENAME_KEY]

    def matchtask(self, file, task):
        if task["action"]["__ansible_module__"] in ['shell', 'command']:
            return any([arg not in self.expected_args for arg in task['action']] +
                       ["=" in task['action']['__ansible_arguments__'][0]])
