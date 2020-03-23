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

import unittest

from ansiblelint import RulesCollection
from ansiblelint.rules.NestedJinjaRule import NestedJinjaRule
from test import RunFromText

FAIL_TASKS = '''
- name: one-level nesting
  set_fact:
    variable_one: "2*(1+2) is {{ 2 * {{ 1 + 2 }} }}"

- name: two-level nesting
  set_fact:
    variable_two: "2*(1+(3-1)) is {{ 2 * {{ 1 + {{ 3 - 1 }} }} }}"

- name: five-level wild nesting
  set_fact:
    variable_three: "{{ {{ {{ {{ {{ 234 }} }} }} }} }}"
'''

SUCCESS_TASKS = '''
- name: proper nesting
  set_fact:
    variable_one: "number for 'one' is {{ 2 * 1 }}"

- name: proper nesting far from each other
  set_fact:
    variable_two: "number for 'two' is {{ 2 * 1 }} and number for 'three' is {{ 4 - 1 }}"

- name: proper nesting close to each other
  set_fact:
    variable_three: "number for 'ten' is {{ 2 - 1 }}{{ 3 - 3 }}"
'''


class TestNestedJinjaRule(unittest.TestCase):
    collection = RulesCollection()
    collection.register(NestedJinjaRule())

    def setUp(self):
        self.runner = RunFromText(self.collection)

    def test_fail(self):
        results = self.runner.run_role_tasks_main(FAIL_TASKS)
        self.assertEqual(3, len(results))

    def test_success(self):
        results = self.runner.run_role_tasks_main(SUCCESS_TASKS)
        self.assertEqual(0, len(results))
