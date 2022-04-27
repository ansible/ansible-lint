"""Tests for no-prompting rule."""
from ansiblelint.config import options
from ansiblelint.rules import RulesCollection
from ansiblelint.rules.no_prompting import NoPromptingRule
from ansiblelint.testing import RunFromText

FAIL_TASKS = """
---
- hosts: all
  vars_prompt:

    - name: username
      prompt: What is your username?
      private: no

    - name: password
      prompt: What is your password?

  tasks:
    - name: Pause for 5 minutes to build app cache
      pause:
        minutes: 5

    - name: A helpful reminder of what to look out for post-update
      ansible.builtin.pause:
        prompt: "Make sure org.foo.FooOverload exception is not present"
"""


def test_no_prompting_fail() -> None:
    """Negative test for no-prompting."""
    # For testing we want to manually enable opt-in rules
    options.enable_list = ["no-prompting"]
    collection = RulesCollection(options=options)
    collection.register(NoPromptingRule())
    runner = RunFromText(collection)
    results = runner.run_playbook(FAIL_TASKS)
    assert len(results) == 3
    assert "Play uses vars_prompt" in str(results)
