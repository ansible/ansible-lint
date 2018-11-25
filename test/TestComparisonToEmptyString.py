import unittest

from ansiblelint import RulesCollection
from ansiblelint.rules.ComparisonToEmptyStringRule import (
    ComparisonToEmptyStringRule)
from test import RunFromText

PASS_WHEN = '''
- name: shut down
  command: /sbin/shutdown -t now
  when: ansible_os_family
'''

FAIL_IS_EMPTY = '''
- hosts: all
  tasks:
  - name: shut down
    command: /sbin/shutdown -t now
    when: ansible_os_family == ""
'''

FAIL_IS_NOT_EMPTY = '''
- name: shut down
  command: /sbin/shutdown -t now
  when: ansible_os_family != ""
'''


class TestComparisonToEmptyStringRule(unittest.TestCase):
    collection = RulesCollection()
    collection.register(ComparisonToEmptyStringRule())

    def setUp(self):
        self.runner = RunFromText(self.collection)

    def test_compare_when(self):
        results = self.runner.run_role_tasks_main(PASS_WHEN)
        self.assertEqual(0, len(results))

    def test_compare_is_empty(self):
        results = self.runner.run_playbook(FAIL_IS_EMPTY)
        self.assertEqual(1, len(results))

    def test_compare_is_not_empty(self):
        results = self.runner.run_role_tasks_main(FAIL_IS_NOT_EMPTY)
        self.assertEqual(1, len(results))
