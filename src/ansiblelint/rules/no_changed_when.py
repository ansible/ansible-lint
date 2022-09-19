"""Implementation of the no-changed-when rule."""
# Copyright (c) 2016 Will Thames <will@thames.id.au>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable


class CommandHasChangesCheckRule(AnsibleLintRule):
    """Commands should not change things if nothing needs doing."""

    id = "no-changed-when"
    description = """
Tasks should tell Ansible when to return ``changed``, unless the task only reads
information. To do this, set ``changed_when``, use the ``creates`` or
``removes`` argument, or use ``when`` to run the task only if another check has
a particular result.

For example, this task registers the ``shell`` output and uses the return code
to define when the task has changed.

```yaml
    - name: Handle shell output with return code
      ansible.builtin.shell: cat {{ my_file|quote }}
      register: my_output
      changed_when: my_output.rc != 0
```

The following example will trigger the rule since the task does not
handle the output of the ``command``.

```yaml
    - name: Does not handle any output or return codes
      ansible.builtin.command: cat {{ my_file|quote }}
```
    """
    severity = "HIGH"
    tags = ["command-shell", "idempotency"]
    version_added = "historic"

    _commands = ["command", "shell", "raw"]

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> bool | str:
        # tasks in a block are "meta" type
        if task["__ansible_action_type__"] in ["task", "meta"]:
            if task["action"]["__ansible_module__"] in self._commands:
                return (
                    "changed_when" not in task
                    and "when" not in task
                    and "creates" not in task["action"]
                    and "removes" not in task["action"]
                )
        return False


if "pytest" in sys.modules:
    import pytest

    NO_CHANGE_COMMAND_RC = """
- hosts: all
  tasks:
    - name: Handle command output with return code
      ansible.builtin.command: cat {{ my_file|quote }}
      register: my_output
      changed_when: my_output.rc != 0
"""

    NO_CHANGE_SHELL_RC = """
- hosts: all
  tasks:
    - name: Handle shell output with return code
      ansible.builtin.shell: cat {{ my_file|quote }}
      register: my_output
      changed_when: my_output.rc != 0
"""

    NO_CHANGE_SHELL_FALSE = """
- hosts: all
  tasks:
    - name: Handle shell output with false changed_when
      ansible.builtin.shell: cat {{ my_file|quote }}
      register: my_output
      changed_when: false
"""

    NO_CHANGE_ARGS = """
- hosts: all
  tasks:
    - name: Command with argument
      command: createfile.sh
      args:
        creates: /tmp/????unknown_files????
"""

    NO_CHANGE_REGISTER_FAIL = """
- hosts: all
  tasks:
    - name: Register command output, but cat still does not change anything
      ansible.builtin.command: cat {{ my_file|quote }}
      register: my_output
"""

    # also test to ensure it catches tasks in nested blocks.
    NO_CHANGE_COMMAND_FAIL = """
- hosts: all
  tasks:
    - block:
        - block:
            - name: Basic command task, should fail
              ansible.builtin.command: cat my_file
"""

    NO_CHANGE_SHELL_FAIL = """
- hosts: all
  tasks:
    - name: Basic shell task, should fail
      shell: cat my_file
"""

    @pytest.mark.parametrize(
        "rule_runner", (CommandHasChangesCheckRule,), indirect=["rule_runner"]
    )
    def test_no_change_command_rc(rule_runner: Any) -> None:
        """This should pass since ``*_when`` is used."""
        results = rule_runner.run_playbook(NO_CHANGE_COMMAND_RC)
        assert len(results) == 0

    @pytest.mark.parametrize(
        "rule_runner", (CommandHasChangesCheckRule,), indirect=["rule_runner"]
    )
    def test_no_change_shell_rc(rule_runner: Any) -> None:
        """This should pass since ``*_when`` is used."""
        results = rule_runner.run_playbook(NO_CHANGE_SHELL_RC)
        assert len(results) == 0

    @pytest.mark.parametrize(
        "rule_runner", (CommandHasChangesCheckRule,), indirect=["rule_runner"]
    )
    def test_no_change_shell_false(rule_runner: Any) -> None:
        """This should pass since ``*_when`` is used."""
        results = rule_runner.run_playbook(NO_CHANGE_SHELL_FALSE)
        assert len(results) == 0

    @pytest.mark.parametrize(
        "rule_runner", (CommandHasChangesCheckRule,), indirect=["rule_runner"]
    )
    def test_no_change_args(rule_runner: Any) -> None:
        """This test should not pass since the command doesn't do anything."""
        results = rule_runner.run_playbook(NO_CHANGE_ARGS)
        assert len(results) == 0

    @pytest.mark.parametrize(
        "rule_runner", (CommandHasChangesCheckRule,), indirect=["rule_runner"]
    )
    def test_no_change_register_fail(rule_runner: Any) -> None:
        """This test should not pass since cat still doesn't do anything."""
        results = rule_runner.run_playbook(NO_CHANGE_REGISTER_FAIL)
        assert len(results) == 1

    @pytest.mark.parametrize(
        "rule_runner", (CommandHasChangesCheckRule,), indirect=["rule_runner"]
    )
    def test_no_change_command_fail(rule_runner: Any) -> None:
        """This test should fail because command isn't handled."""
        # this also ensures that this catches tasks in nested blocks
        results = rule_runner.run_playbook(NO_CHANGE_COMMAND_FAIL)
        assert len(results) == 1

    @pytest.mark.parametrize(
        "rule_runner", (CommandHasChangesCheckRule,), indirect=["rule_runner"]
    )
    def test_no_change_shell_fail(rule_runner: Any) -> None:
        """This test should fail because shell isn't handled.."""
        results = rule_runner.run_playbook(NO_CHANGE_SHELL_FAIL)
        assert len(results) == 1
