import unittest

from ansible import __version__ as ansible_version_str
import pytest

from ansiblelint import RulesCollection
from ansiblelint.rules.DeprecatedModuleRule import DeprecatedModuleRule
from test import RunFromText


ANSIBLE_MAJOR_VERSION = tuple(map(int, ansible_version_str.split('.')[:2]))


MODULE_DEPRECATED = '''
- name: task example
  docker:
    debug: test
'''


class TestDeprecatedModuleRule(unittest.TestCase):
    collection = RulesCollection()
    collection.register(DeprecatedModuleRule())

    def setUp(self):
        self.runner = RunFromText(self.collection)

    @pytest.mark.xfail(
        ANSIBLE_MAJOR_VERSION > (2, 9),
        reason='Ansible devel has changed so ansible-lint needs fixing. '
        'Ref: https://github.com/ansible/ansible-lint/issues/675',
        raises=SystemExit, strict=True,
    )
    def test_module_deprecated(self):
        results = self.runner.run_role_tasks_main(MODULE_DEPRECATED)
        self.assertEqual(1, len(results))
