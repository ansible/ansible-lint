import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.TaskNoLocalAction import TaskNoLocalAction

from . import RunFromText

TASK_LOCAL_ACTION = '''
- name: task example
  local_action:
    module: boto3_facts
'''


class TestTaskNoLocalAction(unittest.TestCase):
    collection = RulesCollection()
    collection.register(TaskNoLocalAction())

    def setUp(self):
        self.runner = RunFromText(self.collection)

    def test_local_action(self):
        results = self.runner.run_role_tasks_main(TASK_LOCAL_ACTION)
        self.assertEqual(1, len(results))
