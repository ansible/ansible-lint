"""Test Ansible Syntax.

This module contains tests that validate that linter does not produce errors
when encountering what counts as valid Ansible syntax.
"""
from ansiblelint.testing import RunFromText

PB_WITH_NULL_TASKS = '''\
- hosts: all
  tasks:
'''


def test_null_tasks(default_text_runner: RunFromText) -> None:
    """Assure we do not fail when encountering null tasks."""
    results = default_text_runner.run_playbook(PB_WITH_NULL_TASKS)
    assert not results
