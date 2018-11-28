import unittest

from ansiblelint import RulesCollection
from ansiblelint.rules.DeprecatedModuleRule import DeprecatedModuleRule
from test import RunFromText

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

    def test_module_deprecated(self):
        results = self.runner.run_role_tasks_main(MODULE_DEPRECATED)
        self.assertEqual(1, len(results))
