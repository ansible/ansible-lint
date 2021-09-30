# -*- coding: utf-8 -*-
# Author: Adrián Tóth <adtoth@redhat.com>
#
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
from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest

from ansiblelint.file_utils import Lintable
from ansiblelint.runner import Runner

FAIL_TASK_1LN = Lintable(
    'playbook.yml',
    '''\
- hosts: all
  tasks:
    - name: one-level nesting
      set_fact:
        var_one: "2*(1+2) is {{ 2 * {{ 1 + 2 }} }}"
''',
)

FAIL_TASK_1LN_M = Lintable(
    'playbook.yml',
    '''\
- hosts: all
  tasks:
    - name: one-level multiline nesting
      set_fact:
        var_one_ml: >
          2*(1+2) is {{ 2 *
          {{ 1 + 2 }}
          }}
''',
)

FAIL_TASK_2LN = Lintable(
    'playbook.yml',
    '''\
- hosts: all
  tasks:
    - name: two-level nesting
      set_fact:
        var_two: "2*(1+(3-1)) is {{ 2 * {{ 1 + {{ 3 - 1 }} }} }}"
''',
)

FAIL_TASK_2LN_M = Lintable(
    'playbook.yml',
    '''\
- hosts: all
  tasks:
    - name: two-level multiline nesting
      set_fact:
        var_two_ml: >
          2*(1+(3-1)) is {{ 2 *
          {{ 1 +
          {{ 3 - 1 }}
          }} }}
''',
)

FAIL_TASK_W_5LN = Lintable(
    'playbook.yml',
    '''\
- hosts: all
  tasks:
    - name: five-level wild nesting
      set_fact:
        var_three_wld: "{{ {{ {{ {{ {{ 234 }} }} }} }} }}"
''',
)

FAIL_TASK_W_5LN_M = Lintable(
    'playbook.yml',
    '''\
- hosts: all
  tasks:
    - name: five-level wild multiline nesting
      set_fact:
        var_three_wld_ml: >
          {{
          {{
          {{
          {{
          {{ 234 }}
          }}
          }}
          }}
          }}
''',
)

SUCCESS_TASK_P = Lintable(
    'playbook.yml',
    '''\
- hosts: all
  tasks:
    - name: non-nested example
      set_fact:
        var_one: "number for 'one' is {{ 2 * 1 }}"
''',
)

SUCCESS_TASK_P_M = Lintable(
    'playbook.yml',
    '''\
- hosts: all
  tasks:
    - name: multiline non-nested example
      set_fact:
        var_one_ml: >
          number for 'one' is {{
          2 * 1 }}
''',
)

SUCCESS_TASK_2P = Lintable(
    'playbook.yml',
    '''\
- hosts: all
  tasks:
    - name: nesting far from each other
      set_fact:
        var_two: "number for 'two' is {{ 2 * 1 }} and number for 'three' is {{ 4 - 1 }}"
''',
)

SUCCESS_TASK_2P_M = Lintable(
    'playbook.yml',
    '''\
- hosts: all
  tasks:
    - name: multiline nesting far from each other
      set_fact:
        var_two_ml: >
          number for 'two' is {{ 2 * 1
          }} and number for 'three' is {{
          4 - 1 }}
''',
)

SUCCESS_TASK_C_2P = Lintable(
    'playbook.yml',
    '''\
- hosts: all
  tasks:
    - name: nesting close to each other
      set_fact:
        var_three: "number for 'ten' is {{ 2 - 1 }}{{ 3 - 3 }}"
''',
)

SUCCESS_TASK_C_2P_M = Lintable(
    'playbook.yml',
    '''\
- hosts: all
  tasks:
    - name: multiline nesting close to each other
      set_fact:
        var_three_ml: >
          number for 'ten' is {{
          2 - 1
          }}{{ 3 - 3 }}
''',
)

SUCCESS_TASK_PRINT = Lintable(
    'playbook.yml',
    '''\
- hosts: all
  tasks:
    - name: print curly braces
      debug:
        msg: docker image inspect my_image --format='{{'{{'}}.Size{{'}}'}}'
''',
)


@pytest.fixture
def _playbook_file(tmp_path: Path, request: SubRequest) -> None:
    if request.param is None:
        return
    for play_file in request.param:
        p = tmp_path / play_file.name
        p.write_text(play_file.content)


@pytest.mark.parametrize(
    '_playbook_file',
    (
        pytest.param([FAIL_TASK_1LN], id='file includes one-level nesting'),
        pytest.param([FAIL_TASK_1LN_M], id='file includes one-level multiline nesting'),
        pytest.param([FAIL_TASK_2LN], id='file includes two-level nesting'),
        pytest.param([FAIL_TASK_2LN_M], id='file includes two-level multiline nesting'),
        pytest.param([FAIL_TASK_W_5LN], id='file includes five-level wild nesting'),
        pytest.param(
            [FAIL_TASK_W_5LN_M], id='file includes five-level wild multiline nesting'
        ),
    ),
    indirect=['_playbook_file'],
)
@pytest.mark.usefixtures('_playbook_file')
def test_including_wrong_nested_jinja(runner: Runner) -> None:
    """Check that broken Jinja nesting produces a violation."""
    rule_violations = runner.run()
    assert rule_violations[0].rule.id == 'no-jinja-nesting'


@pytest.mark.parametrize(
    '_playbook_file',
    (
        pytest.param([SUCCESS_TASK_P], id='file includes non-nested example'),
        pytest.param(
            [SUCCESS_TASK_P_M], id='file includes multiline non-nested example'
        ),
        pytest.param([SUCCESS_TASK_2P], id='file includes nesting far from each other'),
        pytest.param(
            [SUCCESS_TASK_2P_M],
            id='file includes multiline nesting far from each other',
        ),
        pytest.param(
            [SUCCESS_TASK_C_2P], id='file includes nesting close to each other'
        ),
        pytest.param(
            [SUCCESS_TASK_C_2P_M],
            id='file includes multiline nesting close to each other',
        ),
        pytest.param([SUCCESS_TASK_PRINT], id='file includes print curly braces'),
    ),
    indirect=['_playbook_file'],
)
@pytest.mark.usefixtures('_playbook_file')
def test_including_proper_nested_jinja(runner: Runner) -> None:
    """Check that properly balanced Jinja nesting doesn't fail."""
    rule_violations = runner.run()
    assert not rule_violations
