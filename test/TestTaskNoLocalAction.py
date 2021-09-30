# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.TaskNoLocalAction import TaskNoLocalAction
from ansiblelint.testing import RunFromText

TASK_LOCAL_ACTION = '''
- name: task example
  local_action:
    module: boto3_facts
'''


class TestTaskNoLocalAction(unittest.TestCase):
    collection = RulesCollection()
    collection.register(TaskNoLocalAction())

    def setUp(self) -> None:
        self.runner = RunFromText(self.collection)

    def test_local_action(self) -> None:
        results = self.runner.run_role_tasks_main(TASK_LOCAL_ACTION)
        assert len(results) == 1
