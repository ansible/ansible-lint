import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.ShellWithoutPipefail import ShellWithoutPipefail

from . import RunFromText

FAIL_TASKS = '''
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
'''

SUCCESS_TASKS = '''
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
'''


class TestShellWithoutPipeFail(unittest.TestCase):
    collection = RulesCollection()
    collection.register(ShellWithoutPipefail())

    def setUp(self):
        self.runner = RunFromText(self.collection)

    def test_fail(self):
        results = self.runner.run_playbook(FAIL_TASKS)
        self.assertEqual(3, len(results))

    def test_success(self):
        results = self.runner.run_playbook(SUCCESS_TASKS)
        self.assertEqual(0, len(results))
