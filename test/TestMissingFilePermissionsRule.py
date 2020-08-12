# Copyright (c) 2020 Sorin Sbarnea <sorin.sbarnea@gmail.com>
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
"""MissingFilePermissionsRule tests."""
import pytest

from ansiblelint.rules.MissingFilePermissionsRule import MissingFilePermissionsRule

SUCCESS_TASKS = '''
---
- hosts: hosts
  tasks:
    - name: permissions not missing and string
      file:
        path: foo
        mode: preserve
    - name: permissions not missing and numeric
      file:
        path: foo
        mode: 0600
    - name: permissions missing while state is absent is fine
      file:
        path: foo
        state: absent
'''

FAIL_TASKS = '''
---
- hosts: hosts
  tasks:
    - name: permissions missing
      file:
        path: foo
'''


@pytest.mark.parametrize('rule_runner', (MissingFilePermissionsRule, ), indirect=['rule_runner'])
def test_success(rule_runner):
    """Validate that mode presence avoids hitting the rule."""
    results = rule_runner.run_playbook(SUCCESS_TASKS)
    assert len(results) == 0


@pytest.mark.parametrize('rule_runner', (MissingFilePermissionsRule, ), indirect=['rule_runner'])
def test_fail(rule_runner):
    """Validate that missing mode triggers the rule."""
    results = rule_runner.run_playbook(FAIL_TASKS)
    assert len(results) == 1
