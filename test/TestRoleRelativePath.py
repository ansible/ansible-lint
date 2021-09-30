# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.RoleRelativePath import RoleRelativePath
from ansiblelint.testing import RunFromText

FAIL_TASKS = '''
- name: template example
  template:
    src: ../templates/foo.j2
    dest: /etc/file.conf
- name: copy example
  copy:
    src: ../files/foo.conf
    dest: /etc/foo.conf
# Removed from test suite as module is no longer part of core
# - name: win_template example
#   win_template:
#     src: ../win_templates/file.conf.j2
#     dest: file.conf
# - name: win_copy example
#   win_copy:
#     src: ../files/foo.conf
#     dest: renamed-foo.conf
'''

SUCCESS_TASKS = '''
- name: content example with no src
  copy:
    content: '# This file was moved to /etc/other.conf'
    dest: /etc/mine.conf
# - name: content example with no src
#   win_copy:
#     content: '# This file was moved to /etc/other.conf'
#     dest: /etc/mine.conf
'''


class TestRoleRelativePath(unittest.TestCase):
    collection = RulesCollection()
    collection.register(RoleRelativePath())

    def setUp(self) -> None:
        self.runner = RunFromText(self.collection)

    def test_fail(self) -> None:
        results = self.runner.run_role_tasks_main(FAIL_TASKS)
        assert len(results) == 2

    def test_success(self) -> None:
        results = self.runner.run_role_tasks_main(SUCCESS_TASKS)
        assert len(results) == 0
