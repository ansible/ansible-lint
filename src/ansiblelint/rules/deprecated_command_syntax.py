"""Implementation of deprecated-command-syntax rule."""
# Copyright (c) 2013-2014 Will Thames <will@thames.id.au>
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

import os
import sys
from typing import TYPE_CHECKING, Any

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.utils import convert_to_boolean, get_first_cmd_arg

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable


class CommandsInsteadOfArgumentsRule(AnsibleLintRule):
    """Using command rather than an argument to e.g. file."""

    id = "deprecated-command-syntax"
    description = (
        "Executing a command when there are arguments to modules "
        "is generally a bad idea"
    )
    severity = "VERY_HIGH"
    tags = ["command-shell", "deprecations"]
    version_added = "historic"

    _commands = ["command", "shell", "raw"]
    _arguments = {
        "chown": "owner",
        "chmod": "mode",
        "chgrp": "group",
        "ln": "state=link",
        "mkdir": "state=directory",
        "rmdir": "state=absent",
        "rm": "state=absent",
    }

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> bool | str:
        if task["action"]["__ansible_module__"] in self._commands:
            first_cmd_arg = get_first_cmd_arg(task)
            if not first_cmd_arg:
                return False

            executable = os.path.basename(first_cmd_arg)
            if executable in self._arguments and convert_to_boolean(
                task["action"].get("warn", True)
            ):
                message = "{0} used in place of argument {1} to file module"
                return message.format(executable, self._arguments[executable])
        return False


DEPRECATED_COMMAND_PLAY = """---
- name: Fixture
  hosts: localhost
  tasks:
  - name: Shell with pipe
    ansible.builtin.command:
      err: echo hello | true  # noqa: risky-shell-pipe
    changed_when: false
"""


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    import pytest

    from ansiblelint.testing import RunFromText  # pylint: disable=ungrouped-imports

    @pytest.mark.parametrize(
        ("text", "expected"),
        (pytest.param(DEPRECATED_COMMAND_PLAY, 0, id="no_first_cmd_arg"),),
    )
    def test_rule_deprecated_command_no_first_cmd_arg(
        default_text_runner: RunFromText, text: str, expected: int
    ) -> None:
        """Validate that rule works as intended."""
        results = default_text_runner.run_playbook(text)
        assert len(results) == expected
