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
    id = 'ANSIBLE0009'
    shortdesc = 'Octal file permissions must contain leading zero'
    description = 'Numeric file permissions without leading zero can behave' + \
        'in unexpected ways. See ' + \
        'http://docs.ansible.com/ansible/file_module.html'
    tags = ['formatting']

    _modules = ['assemble', 'copy', 'file', 'ini_file', 'lineinfile',
                'replace', 'synchronize', 'template', 'unarchive']

    mode_regex = re.compile(r'^\s*[0-9]+\s*$')
    valid_mode_regex = re.compile(r'^\s*0[0-7]{3,4}\s*$')

    def matchtask(self, file, task):
        if task["action"]["module"] in self._modules:
            mode = task['action'].get('mode', None)
            if isinstance(mode, basestring) and self.mode_regex.match(mode):
                return not self.valid_mode_regex.match(mode)
            if isinstance(mode, int):
                # sensible file permission modes don't
                # have write or execute bit set when read bit is
                # not set
                # also, user permissions are more generous than
                # group permissions and user and group permissions
                # are more generous than world permissions

                result = (mode % 8 and mode % 8 < 4 or
                          (mode >> 3) % 8 and (mode >> 3) % 8 < 4 or
                          (mode >> 6) % 8 and (mode >> 6) % 8 < 4 or
                          mode & 8 < (mode << 3) & 8 or
                          mode & 8 < (mode << 6) & 8 or
                          (mode << 3) & 8 < (mode << 6) & 8)

                return result
