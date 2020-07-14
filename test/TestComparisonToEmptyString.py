import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.ComparisonToEmptyStringRule import ComparisonToEmptyStringRule

from . import RunFromText

SUCCESS_TASKS = '''
- name: shut down
  command: /sbin/shutdown -t now
  when: ansible_os_family
'''

FAIL_TASKS = '''
- hosts: all
  tasks:
  - name: shut down
    command: /sbin/shutdown -t now
    when: ansible_os_family == ""
  - name: shut down
    command: /sbin/shutdown -t now
    when: ansible_os_family !=""
'''


class TestComparisonToEmptyStringRule(unittest.TestCase):
    collection = RulesCollection()
    collection.register(ComparisonToEmptyStringRule())

    def setUp(self):
        self.runner = RunFromText(self.collection)

    def test_success(self):
        results = self.runner.run_role_tasks_main(SUCCESS_TASKS)
        self.assertEqual(0, len(results))

    def test_fail(self):
        results = self.runner.run_playbook(FAIL_TASKS)
        self.assertEqual(2, len(results))
