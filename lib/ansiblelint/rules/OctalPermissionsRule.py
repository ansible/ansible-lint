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

from ansiblelint.rules import AnsibleLintRule


class OctalPermissionsRule(AnsibleLintRule):
    id = '202'
    shortdesc = 'Octal file permissions must contain leading zero or be a string'
    description = (
        'Numeric file permissions without leading zero can behave '
        'in unexpected ways. See '
        'http://docs.ansible.com/ansible/file_module.html'
    )
    severity = 'VERY_HIGH'
    tags = ['formatting', 'ANSIBLE0009']
    version_added = 'historic'

    _modules = ['assemble', 'copy', 'file', 'ini_file', 'lineinfile',
                'replace', 'synchronize', 'template', 'unarchive']

    def is_invalid_permission(self, mode):
        # sensible file permission modes don't
        # have write bit set when read bit is
        # not set and don't have execute bit set
        # when user execute bit is not set.
        # also, user permissions are more generous than
        # group permissions and user and group permissions
        # are more generous than world permissions

        other_write_without_read = (mode % 8 and mode % 8 < 4 and
                                    not (mode % 8 == 1 and (mode >> 6) % 2 == 1))
        group_write_without_read = ((mode >> 3) % 8 and (mode >> 3) % 8 < 4 and
                                    not ((mode >> 3) % 8 == 1 and (mode >> 6) % 2 == 1))
        user_write_without_read = ((mode >> 6) % 8 and (mode >> 6) % 8 < 4 and
                                   not (mode >> 6) % 8 == 1)
        other_more_generous_than_group = mode % 8 > (mode >> 3) % 8
        other_more_generous_than_user = mode % 8 > (mode >> 6) % 8
        group_more_generous_than_user = (mode >> 3) % 8 > (mode >> 6) % 8

        return (other_write_without_read or
                group_write_without_read or
                user_write_without_read or
                other_more_generous_than_group or
                other_more_generous_than_user or
                group_more_generous_than_user)

    def matchtask(self, file, task):
        if task["action"]["__ansible_module__"] in self._modules:
            mode = task['action'].get('mode', None)

            if isinstance(mode, str):
                return False

            if isinstance(mode, int):
                return self.is_invalid_permission(mode)
