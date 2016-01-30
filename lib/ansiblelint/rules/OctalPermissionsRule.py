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

from ansiblelint import AnsibleLintRule
import re

class OctalPermissionsRule(AnsibleLintRule):
    id = 'ANSIBLE0008'
    shortdesc = 'Octal file permissions must contain leading zero'
    description = 'Numeric file permissions without leading zero can behave' + \
            'in unexpected ways. See ' + \
            'http://docs.ansible.com/ansible/file_module.html'
    tags = ['formatting']
    digits_regex = re.compile(r'[0-9]+')
    valid_permissions_regex = re.compile(r'0[0-7]{3}')

    def matchtask(self, file, task):
        try:
            mode_str = str(task['action']['mode'])
            # If it is a numeric permission,
            if re.match(self.digits_regex, mode_str):
                # Return the inverse of if it's valid
                return not re.match(self.valid_permissions_regex, mode_str)
        # If the task didn't have a 'mode' argument, it can't be wrong
        except KeyError:
            return False
