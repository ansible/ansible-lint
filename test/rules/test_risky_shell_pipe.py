"""Tests for risky-shell-pile rule."""
from ansiblelint.rules import RulesCollection
from ansiblelint.rules.risky_shell_pipe import ShellWithoutPipefail
from ansiblelint.testing import RunFromText

FAIL_TASKS = """
---
- hosts: localhost
  become: no
  tasks:
    - name: Pipeline without pipefail
      shell: false | cat

    - name: Pipeline with or and pipe, no pipefail
      shell: false || true | cat

    - shell: |
        df | grep '/dev'
"""

SUCCESS_TASKS = """
---
- hosts: localhost
  become: no
  tasks:
    - name: Pipeline with pipefail
      shell: set -o pipefail && false | cat

    - name: Pipeline with pipefail, multi-line
      shell: |
        set -o pipefail
        false | cat

    - name: Pipeline with pipefail, complex set
      shell: |
        set -e -x -o pipefail
        false | cat

    - name: Pipeline with pipefail, complex set
      shell: |
        set -e -x -o pipefail
        false | cat

    - name: Pipeline with pipefail, complex set
      shell: |
        set -eo pipefail
        false | cat

    - name: Pipeline with pipefail not at first line
      shell: |
        echo foo
        set -eo pipefail
        false | cat

    - name: Pipeline without pipefail, ignoring errors
      shell: false | cat
      ignore_errors: true

    - name: Non-pipeline without pipefail
      shell: "true"

    - name: Command without pipefail
      command: "true"

    - name: Shell with or
      shell:
        false || true

    - shell: |
        set -o pipefail
        df | grep '/dev'

    - name: Should not fail due to ignore_errors being true
      shell: false | cat
      ignore_errors: true
"""


def test_fail() -> None:
    """Negative test for risky-shell-pipe."""
    collection = RulesCollection()
    collection.register(ShellWithoutPipefail())
    runner = RunFromText(collection)
    results = runner.run_playbook(FAIL_TASKS)
    assert len(results) == 3


def test_success() -> None:
    """Positive test for risky-shell-pipe."""
    collection = RulesCollection()
    collection.register(ShellWithoutPipefail())
    runner = RunFromText(collection)
    results = runner.run_playbook(SUCCESS_TASKS)
    assert len(results) == 0
