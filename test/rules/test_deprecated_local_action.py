"""Tests for deprecated-local-action rule."""
from ansiblelint.rules import RulesCollection
from ansiblelint.rules.deprecated_local_action import TaskNoLocalAction
from ansiblelint.testing import RunFromText

TASK_LOCAL_ACTION = """
- name: task example
  local_action:
    module: boto3_facts
"""


def test_local_action() -> None:
    """Positive test deprecated_local_action."""
    collection = RulesCollection()
    collection.register(TaskNoLocalAction())
    runner = RunFromText(collection)
    results = runner.run_role_tasks_main(TASK_LOCAL_ACTION)
    assert len(results) == 1
