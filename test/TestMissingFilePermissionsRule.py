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

SUCCESS_TASKS = '''\
---
- hosts: hosts
  tasks:
    - name: permissions not missing and numeric
      file:
        path: foo
        mode: 0600
    - name: permissions missing while state is absent is fine
      file:
        path: foo
        state: absent
    - name: permissions missing while state is file (default) is fine
      file:
        path: foo
    - name: permissions missing while state is link is fine
      file:
        path: foo2
        src: foo
        state: link
    - name: file edit when create is false
      lineinfile:
        path: foo
        create: false
        line: some content here
    - name: replace should not require mode
      replace:
        path: foo
    - name: file with recursive does not require mode
      file:
        state: directory
        recurse: yes
'''

FAIL_TASKS = '''\
---
- hosts: hosts
  tasks:
    - name: file does not allow preserve value for mode
      file:
        path: foo
        mode: preserve
    - name: permissions missing and might create file
      file:
        path: foo
        state: touch
    - name: permissions missing and might create directory
      file:
        path: foo
        state: directory
    # - name: permissions needed if create is used
    #   ini_file:
    #     path: foo
    #     create: true
    - name: lineinfile when create is true
      lineinfile:
        path: foo
        create: true
        line: some content here
    - name: replace does not allow preserve mode
      replace:
        path: foo
        mode: preserve
    # - name: ini_file does not accept preserve mode
    #   ini_file:
    #     path: foo
    #     create: true
    #     mode: preserve
'''


@pytest.mark.parametrize('rule_runner', (MissingFilePermissionsRule, ), indirect=['rule_runner'])
def test_success(rule_runner) -> None:
    """Validate that mode presence avoids hitting the rule."""
    results = rule_runner.run_playbook(SUCCESS_TASKS)
    assert len(results) == 0


@pytest.mark.parametrize('rule_runner', (MissingFilePermissionsRule, ), indirect=['rule_runner'])
def test_fail(rule_runner) -> None:
    """Validate that missing mode triggers the rule."""
    results = rule_runner.run_playbook(FAIL_TASKS)
    assert len(results) == 5
    assert results[0].linenumber == 4
    assert results[1].linenumber == 8
    assert results[2].linenumber == 12
    # assert results[3].linenumber == 16
    assert results[3].linenumber == 20
    assert results[4].linenumber == 25
    # assert results[6].linenumber == 29
