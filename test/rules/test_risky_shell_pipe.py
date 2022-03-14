"""Tests for risky-shell-pile rule."""
from ansiblelint.rules import RulesCollection
from ansiblelint.rules.risky_shell_pipe import ShellWithoutPipefail
from ansiblelint.testing import RunFromText

FAIL_TASKS = """
---
- hosts: localhost
  become: no
  tasks:
    - name: pipeline without pipefail
      shell: false | cat

    - name: pipeline with or and pipe, no pipefail
      shell: false || true | cat

    - shell: |
        df | grep '/dev'
"""

SUCCESS_TASKS = """
---
- hosts: localhost
  become: no
  tasks:
    - name: pipeline with pipefail
      shell: set -o pipefail && false | cat

    - name: pipeline with pipefail, multi-line
      shell: |
        set -o pipefail
        false | cat

    - name: pipeline with pipefail, complex set
      shell: |
        set -e -x -o pipefail
        false | cat

    - name: pipeline with pipefail, complex set
      shell: |
        set -e -x -o pipefail
        false | cat

    - name: pipeline with pipefail, complex set
      shell: |
        set -eo pipefail
        false | cat

    - name: pipeline with pipefail not at first line
      shell: |
        echo foo
        set -eo pipefail
        false | cat

    - name: pipeline without pipefail, ignoring errors
      shell: false | cat
      ignore_errors: true

    - name: non-pipeline without pipefail
      shell: "true"

    - name: command without pipefail
      command: "true"

    - name: shell with or
      shell:
        false || true

    - shell: |
        set -o pipefail
        df | grep '/dev'

    - name: should not fail due to ignore_errors being true
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
