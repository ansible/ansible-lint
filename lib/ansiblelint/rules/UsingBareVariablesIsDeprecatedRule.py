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

import re

from jinja2.defaults import VARIABLE_START_STRING, BLOCK_START_STRING

from ansiblelint import AnsibleLintRule


class UsingBareVariablesIsDeprecatedRule(AnsibleLintRule):
    id = 'ANSIBLE0015'
    shortdesc = 'Using bare variables is deprecated'
    description = 'Using bare variables is deprecated. Update your' + \
        'playbooks so that the environment value uses the full variable' + \
        'syntax ("{{your_variable}}").'
    tags = ['formatting']

    _loops = re.compile(r'^with_.*$')

    def matchtask(self, file, task):
        loop_type = next((key for key in task.keys() if self._loops.match(key)), None)

        if loop_type and isinstance(task[loop_type], basestring):
            # Check if the text after "with_" has a '{%' or '{{' to determine if it
            # is wrapped correctly for Ansible 2. This is a similar approach to how
            # it's done in Ansible 2.
            # see https://github.com/ansible/ansible/commit/8716bf8021800a18cb8d6cfea3f296ba4f834692
            with_text = task[loop_type]
            if (BLOCK_START_STRING not in with_text) and (VARIABLE_START_STRING not in with_text):
                message = "Found a bare variable '{0}' used in a '{1}' loop." + \
                          " You should use the full variable syntax ('{{{{{0}}}}}')"
                return message.format(task[loop_type], loop_type)
