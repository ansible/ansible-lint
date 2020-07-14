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

from ansiblelint.rules import AnsibleLintRule


class UseCommandInsteadOfShellRule(AnsibleLintRule):
    id = '305'
    shortdesc = 'Use shell only when shell functionality is required'
    description = (
        'Shell should only be used when piping, redirecting '
        'or chaining commands (and Ansible would be preferred '
        'for some of those!)'
    )
    severity = 'HIGH'
    tags = ['command-shell', 'safety', 'ANSIBLE0013']
    version_added = 'historic'

    def matchtask(self, file, task):
        # Use unjinja so that we don't match on jinja filters
        # rather than pipes
        if task["action"]["__ansible_module__"] == 'shell':
            if 'cmd' in task['action']:
                unjinjad_cmd = self.unjinja(task["action"].get("cmd", []))
            else:
                unjinjad_cmd = self.unjinja(
                    ' '.join(task["action"].get("__ansible_arguments__", [])))
            return not any([ch in unjinjad_cmd for ch in '&|<>;$\n*[]{}?`'])
