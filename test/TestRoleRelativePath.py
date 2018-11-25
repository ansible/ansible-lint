import unittest

from ansiblelint import RulesCollection
from ansiblelint.rules.RoleRelativePath import RoleRelativePath
from test import RunFromText

ROLE_RELATIVE_PATH = '''
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


class TestRoleRelativePath(unittest.TestCase):
    collection = RulesCollection()
    collection.register(RoleRelativePath())

    def setUp(self):
        self.runner = RunFromText(self.collection)

    def test_role_relative_path(self):
        results = self.runner.run_role_tasks_main(ROLE_RELATIVE_PATH)
        self.assertEqual(4, len(results))
