import unittest
import os

from ansiblelint import RulesCollection
from test import RunFromText


ROLE_TASKS = '''
---
- name: test 303
  command: git log
  changed_when: False
- name: test 303 (skipped)
  command: git log # noqa 303
  changed_when: False
'''

ROLE_TASKS_WITH_BLOCK = '''
---
- name: bad git 1  # noqa 401
  action: git a=b c=d
- name: bad git 2
  action: git a=b c=d
- name: Block with rescue and always section
  block:
    - name: bad git 3  # noqa 401
      action: git a=b c=d
    - name: bad git 4
      action: git a=b c=d
  rescue:
    - name: bad git 5  # noqa 401
      action: git a=b c=d
    - name: bad git 6
      action: git a=b c=d
  always:
    - name: bad git 7  # noqa 401
      action: git a=b c=d
    - name: bad git 8
      action: git a=b c=d
'''

PLAYBOOK = '''
- hosts: all
  tasks:
    - name: test 402
      action: hg
    - name: test 402 (skipped)  # noqa 402
      action: hg

    - name: test 401 and 501
      become_user: alice
      action: git
    - name: test 401 and 501 (skipped)  # noqa 401 501
      become_user: alice
      action: git

    - name: test 204 and 206
      get_url:
        url: http://example.com/really_long_path/really_long_path/really_long_path/really_long_path/really_long_path/really_long_path/really_long_path/really_long_path/file.conf
        dest: "{{dest_proj_path}}/foo.conf"
    - name: test 204 and 206 (skipped)
      get_url:
        url: http://example.com/really_long_path/really_long_path/really_long_path/really_long_path/really_long_path/really_long_path/really_long_path/really_long_path/file.conf  # noqa 204
        dest: "{{dest_proj_path}}/foo.conf"  # noqa 206

    - name: test 302
      command: creates=B chmod 644 A
    - name: test 302
      command: warn=yes creates=B chmod 644 A
    - name: test 302 (skipped via no warn)
      command: warn=no creates=B chmod 644 A
    - name: test 302 (skipped via skip_ansible_lint)
      command: creates=B chmod 644 A
      tags:
        - skip_ansible_lint

    - name: test invalid action (skipped)
      foo: bar
      tags:
        - skip_ansible_lint
'''

ROLE_META = '''
galaxy_info:  # noqa 701
  author: your name  # noqa 703
  description: missing min_ansible_version and platforms. author default not changed
  license: MIT
'''


class TestSkipInsideYaml(unittest.TestCase):
    rulesdir = os.path.join('lib', 'ansiblelint', 'rules')
    collection = RulesCollection.create_from_directory(rulesdir)

    def setUp(self):
        self.runner = RunFromText(self.collection)

    def test_role_tasks(self):
        results = self.runner.run_role_tasks_main(ROLE_TASKS)
        self.assertEqual(1, len(results))

    def test_role_tasks_with_block(self):
        results = self.runner.run_role_tasks_main(ROLE_TASKS_WITH_BLOCK)
        self.assertEqual(4, len(results))

    def test_playbook(self):
        results = self.runner.run_playbook(PLAYBOOK)
        self.assertEqual(7, len(results))

    def test_role_meta(self):
        results = self.runner.run_role_meta_main(ROLE_META)
        self.assertEqual(0, len(results))
