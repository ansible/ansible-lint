import unittest

from ansiblelint import RulesCollection
from ansiblelint.rules.RoleRelativePath import RoleRelativePath
from test import RunFromText

from importlib_metadata import version as get_dist_version
from packaging.version import Version
import pytest


FAIL_TASKS = '''
- name: template example
  template:
    src: ../templates/foo.j2
    dest: /etc/file.conf
- name: copy example
  copy:
    src: ../files/foo.conf
    dest: /etc/foo.conf
- name: win_template example
  win_template:
    src: ../win_templates/file.conf.j2
    dest: file.conf
- name: win_copy example
  win_copy:
    src: ../files/foo.conf
    dest: renamed-foo.conf
'''

SUCCESS_TASKS = '''
- name: content example with no src
  copy:
    content: '# This file was moved to /etc/other.conf'
    dest: /etc/mine.conf
- name: content example with no src
  win_copy:
    content: '# This file was moved to /etc/other.conf'
    dest: /etc/mine.conf
'''


class TestRoleRelativePath(unittest.TestCase):
    collection = RulesCollection()
    collection.register(RoleRelativePath())

    def setUp(self):
        self.runner = RunFromText(self.collection)

    @pytest.mark.xfail(
        Version(get_dist_version('ansible')) >= Version('2.10.dev0') and
        Version(get_dist_version('ansible-base')) >= Version('2.10.dev0'),
        reason='Post-split Ansible Core Engine does not have '
        'the module used in the test playbook.'
        ' Ref: https://github.com/ansible/ansible-lint/issues/703.'
        ' Ref: https://github.com/ansible/ansible/pull/68598.',
        raises=SystemExit,
        strict=True,
    )
    def test_fail(self):
        results = self.runner.run_role_tasks_main(FAIL_TASKS)
        self.assertEqual(4, len(results))

    @pytest.mark.xfail(
        Version(get_dist_version('ansible')) >= Version('2.10.dev0') and
        Version(get_dist_version('ansible-base')) >= Version('2.10.dev0'),
        reason='Post-split Ansible Core Engine does not have '
        'the module used in the test playbook.'
        ' Ref: https://github.com/ansible/ansible-lint/issues/703.'
        ' Ref: https://github.com/ansible/ansible/pull/68598.',
        raises=SystemExit,
        strict=True,
    )
    def test_success(self):
        results = self.runner.run_role_tasks_main(SUCCESS_TASKS)
        self.assertEqual(0, len(results))
