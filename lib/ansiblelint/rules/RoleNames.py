# Copyright (c) 2020 Gael Chamoulaud <gchamoul@redhat.com>
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
from ansiblelint import AnsibleLintRule


class RoleNames(AnsibleLintRule):
    id = '207'
    shortdesc = (
        "Use only lowercase alphanumeric characters, plus '_' and start "
        "with an alpha character in role names"
    )
    description = (
        "Role names are now limited to contain only lowercase alphanumeric "
        "characters, plus '_' and start with an alpha character"
    )
    severity = 'HIGH'
    done = []  # already noticed roles list
    tags = ['formatting']
    version_added = '4.0.0'

    ROLE_NAME_REGEXP = re.compile('^[a-z][a-z0-9_]+$')

    def match(self, file, text):
        # if file['type'] != 'tasks':
        #     return False

        path = file['path'].split("/")
        if "roles" in path:
            role_name = path[path.index("roles") + 1]
            if role_name not in self.done:
                self.done.append(role_name)
                if not re.match(self.ROLE_NAME_REGEXP, role_name):
                    return True
            else:
                return False
        return False
