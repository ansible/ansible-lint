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


def _become_user_without_become(data):
    return 'become_user' in data and 'become' not in data


class BecomeUserWithoutBecomeRule(AnsibleLintRule):
    id = '501'
    shortdesc = 'become_user requires become to work as expected'
    description = '``become_user`` without ``become`` will not actually change user'
    severity = 'VERY_HIGH'
    tags = ['task', 'oddity', 'ANSIBLE0017']
    version_added = 'historic'

    def matchplay(self, file, data):
        if file['type'] == 'playbook' and _become_user_without_become(data):
            return ({'become_user': data}, self.shortdesc)

    def matchtask(self, file, task):
        return _become_user_without_become(task)
