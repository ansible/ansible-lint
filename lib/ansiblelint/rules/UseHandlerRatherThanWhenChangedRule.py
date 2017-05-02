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

import six

from ansiblelint import AnsibleLintRule


def _changed_in_when(item):
    return any(changed in item for changed in
               ['.changed', '|changed', '["changed"]', "['changed']"])


class UseHandlerRatherThanWhenChangedRule(AnsibleLintRule):
    id = 'ANSIBLE0016'
    shortdesc = 'Tasks that run when changed should likely be handlers'
    description = "If a task has a `when: result.changed` setting, it's effectively " \
                  "acting as a handler"
    tags = ['behaviour']

    def matchtask(self, file, task):
        if task["__ansible_action_type__"] == 'task':
            when = task.get('when')
            if isinstance(when, list):
                for item in when:
                    if _changed_in_when(item):
                        return True
            if isinstance(when, six.string_types):
                return _changed_in_when(when)
