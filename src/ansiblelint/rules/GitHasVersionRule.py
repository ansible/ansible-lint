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

from typing import Any, Dict, Union

from ansiblelint.rules import AnsibleLintRule


class GitHasVersionRule(AnsibleLintRule):
    id = '401'
    shortdesc = 'Git checkouts must contain explicit version'
    description = (
        'All version control checkouts must point to '
        'an explicit commit or tag, not just ``latest``'
    )
    severity = 'MEDIUM'
    tags = ['module', 'repeatability']
    version_added = 'historic'

    def matchtask(self, task: Dict[str, Any]) -> Union[bool, str]:
        return bool(task['action']['__ansible_module__'] == 'git' and
                    task['action'].get('version', 'HEAD') == 'HEAD')
