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

import os
import pytest
from collections import namedtuple
from ansiblelint import Runner, RulesCollection

PlayFile = namedtuple('PlayFile', ['name', 'content'])

FAIL_TASK_1LN = PlayFile('playbook.yml', u'''
- name: one-level nesting
  set_fact:
    var_one: "2*(1+2) is {{ 2 * {{ 1 + 2 }} }}"
''')

FAIL_TASK_1LN_M = PlayFile('playbook.yml', u'''
- name: one-level multiline nesting
  set_fact:
    var_one_ml: >
      2*(1+2) is {{ 2 *
      {{ 1 + 2 }}
      }}
''')

FAIL_TASK_2LN = PlayFile('playbook.yml', u'''
- name: two-level nesting
  set_fact:
    var_two: "2*(1+(3-1)) is {{ 2 * {{ 1 + {{ 3 - 1 }} }} }}"
''')

FAIL_TASK_2LN_M = PlayFile('playbook.yml', u'''
- name: two-level multiline nesting
  set_fact:
    var_two_ml: >
      2*(1+(3-1)) is {{ 2 *
      {{ 1 +
      {{ 3 - 1 }}
      }} }}
''')

FAIL_TASK_W_5LN = PlayFile('playbook.yml', u'''
- name: five-level wild nesting
  set_fact:
    var_three_wld: "{{ {{ {{ {{ {{ 234 }} }} }} }} }}"
''')

FAIL_TASK_W_5LN_M = PlayFile('playbook.yml', u'''
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
''')

SUCCESS_TASK_P = PlayFile('playbook.yml', u'''
- name: proper non-nested example
  set_fact:
    var_one: "number for 'one' is {{ 2 * 1 }}"
''')

SUCCESS_TASK_P_M = PlayFile('playbook.yml', u'''
- name: proper multiline non-nested example
  set_fact:
    var_one_ml: >
      number for 'one' is {{
      2 * 1 }}
''')

SUCCESS_TASK_2P = PlayFile('playbook.yml', u'''
- name: proper nesting far from each other
  set_fact:
    var_two: "number for 'two' is {{ 2 * 1 }} and number for 'three' is {{ 4 - 1 }}"
''')

SUCCESS_TASK_2P_M = PlayFile('playbook.yml', u'''
- name: proper multiline nesting far from each other
  set_fact:
    var_two_ml: >
      number for 'two' is {{ 2 * 1
      }} and number for 'three' is {{
      4 - 1 }}
''')

SUCCESS_TASK_C_2P = PlayFile('playbook.yml', u'''
- name: proper nesting close to each other
  set_fact:
    var_three: "number for 'ten' is {{ 2 - 1 }}{{ 3 - 3 }}"
''')

SUCCESS_TASK_C_2P_M = PlayFile('playbook.yml', u'''
- name: proper multiline nesting close to each other
  set_fact:
    var_three_ml: >
      number for 'ten' is {{
      2 - 1
      }}{{ 3 - 3 }}
''')

@pytest.fixture
def play_file_path(tmp_path):
    p = tmp_path / 'playbook.yml'
    return str(p)


@pytest.fixture
def rules():
    rulesdir = os.path.join('lib', 'ansiblelint', 'rules')
    return RulesCollection([rulesdir])


@pytest.fixture
def runner(play_file_path, rules):
    return Runner(rules, play_file_path, [], [], [])


@pytest.fixture
def play_files(tmp_path, request):
    if request.param is None:
        return
    for play_file in request.param:
        p = tmp_path / play_file.name
        p.write_text(play_file.content)


@pytest.mark.parametrize(
    'play_files',
    [pytest.param(
        [
            FAIL_TASK_1LN,
            FAIL_TASK_1LN_M,
            FAIL_TASK_2LN,
            FAIL_TASK_2LN_M,
            FAIL_TASK_W_5LN,
            FAIL_TASK_W_5LN_M
        ],
        id='file includes nested jinja pattern'
    )],
    indirect=['play_files']
)
def test_including_nested_jinja(runner, play_files):
    results = str(runner.run())
    assert 'nested jinja' in results


@pytest.mark.parametrize(
    'play_files',
    [pytest.param(
        [
            SUCCESS_TASK_P,
            SUCCESS_TASK_P_M,
            SUCCESS_TASK_2P,
            SUCCESS_TASK_2P_M,
            SUCCESS_TASK_C_2P,
            SUCCESS_TASK_C_2P_M
        ],
        id='file does not include nested jinja pattern'
    )],
    indirect=['play_files']
)
def test_not_including_nested_jinja(runner, play_files):
    results = str(runner.run())
    assert 'nested jinja' not in results
