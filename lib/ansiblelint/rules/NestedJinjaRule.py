# Copyright (c) 2020, Red Hat, Inc.
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


class NestedJinjaRule(AnsibleLintRule):
    id = '207'
    shortdesc = 'Nested jinja pattern'
    description = (
        'There should not be any nested jinja pattern. '
        'Example (bad): \'{{ list_one + {{ list_two | max }} }}\', '
        'example (good): \'{{ list_one + max(list_two) }}\''
    )
    severity = 'VERY_HIGH'
    tags = ['formatting']
    version_added = 'v4.3.0'

    nested_jinja_pattern = re.compile(r"{{(?:[^{}]*)?{{")

    def matchtask(self, file, task):
        strings = (
            val for key, val in task['action'].items()
            if isinstance(val, str) and not key.startswith('__')
        )

        return any(self.nested_jinja_pattern.search(item) for item in strings)
