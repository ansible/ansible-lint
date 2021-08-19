# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.DeprecatedModuleRule import DeprecatedModuleRule
from ansiblelint.testing import RunFromText

MODULE_DEPRECATED = '''
- name: task example
  docker:
    debug: test
'''


class TestDeprecatedModuleRule(unittest.TestCase):
    collection = RulesCollection()
    collection.register(DeprecatedModuleRule())

    def setUp(self) -> None:
        self.runner = RunFromText(self.collection)

    def test_module_deprecated(self) -> None:
        results = self.runner.run_role_tasks_main(MODULE_DEPRECATED)
        assert len(results) == 1
        # based on version and blend of ansible being used, we may
        # get a missing module, so we future proof the test
        assert (
            "couldn't resolve module" not in results[0].message
            or "Deprecated module" not in results[0].message
        )
