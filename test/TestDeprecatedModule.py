import sys
import unittest

import pytest

from ansiblelint import RulesCollection
from ansiblelint.rules.DeprecatedModuleRule import DeprecatedModuleRule
from test import RunFromText


IS_AT_LEAST_PY38 = sys.version_info[:2] >= (3, 8)


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
        IS_AT_LEAST_PY38, reason='',
        raises=SystemExit, strict=True,
    )
    def test_module_deprecated(self):
        results = self.runner.run_role_tasks_main(MODULE_DEPRECATED)
        self.assertEqual(1, len(results))
