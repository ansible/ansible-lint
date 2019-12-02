import unittest

from ansible import __version__ as ANSIBLE_VERSION
from ansiblelint import RulesCollection
from ansiblelint.rules.SudoRule import SudoRule
import semver
from test import RunFromText

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

    @unittest.skipIf(semver.match(ANSIBLE_VERSION, '>=2.9.0'),
                     "'sudo' not supported in this ansible version range")
    def test_run_role_fail(self):
        results = self.runner.run_role_tasks_main(ROLE_2_ERRORS)
        self.assertEqual(2, len(results))

    @unittest.skipIf(semver.match(ANSIBLE_VERSION, '>=2.9.0'),
                     "'sudo' not supported in this ansible version range")
    def test_run_role_pass(self):
        results = self.runner.run_role_tasks_main(ROLE_0_ERRORS)
        self.assertEqual(0, len(results))

    @unittest.skipIf(semver.match(ANSIBLE_VERSION, '>=2.9.0'),
                     "'sudo' not supported in this ansible version range")
    def test_play_root_and_task_fail(self):
        results = self.runner.run_playbook(PLAY_4_ERRORS)
        self.assertEqual(4, len(results))

    @unittest.skipIf(semver.match(ANSIBLE_VERSION, '>=2.9.0'),
                     "'sudo' not supported in this ansible version range")
    def test_play_task_fail(self):
        results = self.runner.run_playbook(PLAY_1_ERROR)
        self.assertEqual(1, len(results))
