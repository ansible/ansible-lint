# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import unittest

import pytest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.DeprecatedModuleRule import DeprecatedModuleRule
from ansiblelint.testing import ANSIBLE_MAJOR_VERSION, RunFromText

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
        'Ref: https://github.com/ansible-community/ansible-lint/issues/675',
        raises=SystemExit, strict=True,
    )
    def test_module_deprecated(self):
        results = self.runner.run_role_tasks_main(MODULE_DEPRECATED)
        self.assertEqual(1, len(results))
