#  Copyright (c) 2020 Chris Meyers <chris.meyers.fsu@gmail.com>
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


class FileTypeModuleHasMode(AnsibleLintRule):
    id = 'ANSIBLE921'
    shortdesc = "Ensure mode is explicitly set"
    description = "Ensure mode is explicitly set when a new file COULD potentially be created"
    severity = 'HIGH'
    tags = ['mode', 'file']

    _commands = ['acl', 'archive', 'assemble', 'copy', 'fetch', 'file', 'ini_file',
                 'iso_extract', 'lineinfile', 'patch', 'tempfile', 'template', 'unarchive', 'xattr']

    def matchtask(self, file, task):
        if task["action"]["__ansible_module__"] in self._commands:
            if task["action"].get("state", "present") == "absent":
                return False
            return not bool(task["action"].get('mode', False))
        return False
