import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.SudoRule import SudoRule

from . import RunFromText

ROLE_2_ERRORS = '''
- name: test
  debug:
    msg: 'test message'
  sudo: yes
  sudo_user: nobody
'''

ROLE_0_ERRORS = '''
- name: test
  debug:
    msg: 'test message'
  become: yes
  become_user: somebody
'''

PLAY_4_ERRORS = '''
- hosts: all
  sudo: yes
  sudo_user: somebody
  tasks:
  - name: test
    debug:
      msg: 'test message'
    sudo: yes
    sudo_user: nobody
'''

PLAY_1_ERROR = '''
- hosts: all
  tasks:
  - name: test
    debug:
      msg: 'test message'
    sudo: yes
'''


class TestSudoRule(unittest.TestCase):
    collection = RulesCollection()
    collection.register(SudoRule())

    def setUp(self):
        self.runner = RunFromText(self.collection)

    def test_run_role_fail(self):
        results = self.runner.run_role_tasks_main(ROLE_2_ERRORS)
        self.assertEqual(2, len(results))

    def test_run_role_pass(self):
        results = self.runner.run_role_tasks_main(ROLE_0_ERRORS)
        self.assertEqual(0, len(results))

    def test_play_root_and_task_fail(self):
        results = self.runner.run_playbook(PLAY_4_ERRORS)
        self.assertEqual(4, len(results))

    def test_play_task_fail(self):
        results = self.runner.run_playbook(PLAY_1_ERROR)
        self.assertEqual(1, len(results))
