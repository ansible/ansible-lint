"""Implementation of command-instead-of-shell rule."""
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
import sys
from typing import TYPE_CHECKING, Any, Dict, Union

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from typing import Optional

    from ansiblelint.file_utils import Lintable


FAIL_PLAY = """---
- hosts: localhost
  tasks:
  - name: shell no pipe
    ansible.builtin.shell: echo hello
    changed_when: false

  - name: shell with jinja filter
    ansible.builtin.shell: echo {{ "hello"|upper }}
    changed_when: false

  - name: shell with jinja filter (fqcn)
    ansible.builtin.shell: echo {{ "hello"|upper }}
    changed_when: false
"""

SUCCESS_PLAY = """---
- hosts: localhost
  tasks:
  - name: shell with pipe
    ansible.builtin.shell: echo hello | true  # noqa: risky-shell-pipe
    changed_when: false

  - name: shell with redirect
    ansible.builtin.shell: echo hello >  /tmp/hello
    changed_when: false

  - name: chain two shell commands
    ansible.builtin.shell: echo hello && echo goodbye
    changed_when: false

  - name: run commands in succession
    ansible.builtin.shell: echo hello ; echo goodbye
    changed_when: false

  - name: use variables
    ansible.builtin.shell: echo $HOME $USER
    changed_when: false

  - name: use * for globbing
    ansible.builtin.shell: ls foo*
    changed_when: false

  - name: use ? for globbing
    ansible.builtin.shell: ls foo?
    changed_when: false

  - name: use [] for globbing
    ansible.builtin.shell: ls foo[1,2,3]
    changed_when: false

  - name: use shell generator
    ansible.builtin.shell: ls foo{.txt,.xml}
    changed_when: false

  - name: use backticks
    ansible.builtin.shell: ls `ls foo*`
    changed_when: false

  - name: use shell with cmd
    ansible.builtin.shell:
      cmd: |
        set -x
        ls foo?
    changed_when: false
"""


class UseCommandInsteadOfShellRule(AnsibleLintRule):
    """Use shell only when shell functionality is required."""

    id = "command-instead-of-shell"
    description = (
        "Shell should only be used when piping, redirecting "
        "or chaining commands (and Ansible would be preferred "
        "for some of those!)"
    )
    severity = "HIGH"
    tags = ["command-shell", "idiom"]
    version_added = "historic"

    def matchtask(
        self, task: Dict[str, Any], file: "Optional[Lintable]" = None
    ) -> Union[bool, str]:
        # Use unjinja so that we don't match on jinja filters
        # rather than pipes
        if task["action"]["__ansible_module__"] in ["shell", "ansible.builtin.shell"]:
            # Since Ansible 2.4, the `command` module does not accept setting
            # the `executable`. If the user needs to set it, they have to use
            # the `shell` module.
            if "executable" in task["action"]:
                return False

            if "cmd" in task["action"]:
                jinja_stripped_cmd = self.unjinja(task["action"].get("cmd", []))
            else:
                jinja_stripped_cmd = self.unjinja(
                    " ".join(task["action"].get("__ansible_arguments__", []))
                )
            return not any(ch in jinja_stripped_cmd for ch in "&|<>;$\n*[]{}?`")
        return False


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:

    import pytest

    from ansiblelint.testing import RunFromText  # pylint: disable=ungrouped-imports

    @pytest.mark.parametrize(("text", "expected"), ((SUCCESS_PLAY, 0), (FAIL_PLAY, 3)))
    def test_rule_command_instead_of_shell(
        default_text_runner: RunFromText, text: str, expected: int
    ) -> None:
        """Validate that rule works as intended."""
        results = default_text_runner.run_playbook(text)
        for result in results:
            assert result.rule.id == UseCommandInsteadOfShellRule.id, result
        assert len(results) == expected
