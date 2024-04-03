"""Implementation of command-instead-of-module rule."""

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

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.utils import convert_to_boolean, get_first_cmd_arg, get_second_cmd_arg

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task


class CommandsInsteadOfModulesRule(AnsibleLintRule):
    """Using command rather than module."""

    id = "command-instead-of-module"
    description = (
        "Executing a command when there is an Ansible module is generally a bad idea"
    )
    severity = "HIGH"
    tags = ["command-shell", "idiom"]
    version_added = "historic"

    _commands = ["command", "shell"]
    _modules = {
        "apt-get": "apt-get",
        "chkconfig": "service",
        "curl": "get_url or uri",
        "git": "git",
        "hg": "hg",
        "letsencrypt": "acme_certificate",
        "mktemp": "tempfile",
        "mount": "mount",
        "patch": "patch",
        "rpm": "yum or rpm_key",
        "rsync": "synchronize",
        "sed": "template, replace or lineinfile",
        "service": "service",
        "supervisorctl": "supervisorctl",
        "svn": "subversion",
        "systemctl": "systemd",
        "tar": "unarchive",
        "unzip": "unarchive",
        "wget": "get_url or uri",
        "yum": "yum",
    }

    _executable_options = {
        "git": ["branch", "log", "lfs", "rev-parse"],
        "systemctl": [
            "--version",
            "get-default",
            "kill",
            "set-default",
            "set-property",
            "show-environment",
            "status",
        ],
        "yum": ["clean", "history", "info"],
        "rpm": ["--nodeps"],
    }

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> bool | str:
        if task["action"]["__ansible_module__"] not in self._commands:
            return False

        first_cmd_arg = get_first_cmd_arg(task)
        second_cmd_arg = get_second_cmd_arg(task)

        if not first_cmd_arg:
            return False

        executable = Path(first_cmd_arg).name

        if (
            second_cmd_arg
            and executable in self._executable_options
            and second_cmd_arg in self._executable_options[executable]
        ):
            return False

        if executable in self._modules and convert_to_boolean(
            task["action"].get("warn", True),
        ):
            message = "{0} used in place of {1} module"
            return message.format(executable, self._modules[executable])
        return False


if "pytest" in sys.modules:
    import pytest

    # pylint: disable=ungrouped-imports
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    @pytest.mark.parametrize(
        ("file", "expected"),
        (
            pytest.param(
                "examples/playbooks/rule-command-instead-of-module-pass.yml",
                0,
                id="pass",
            ),
            pytest.param(
                "examples/playbooks/rule-command-instead-of-module-fail.yml",
                3,
                id="fail",
            ),
        ),
    )
    def test_command_instead_of_module(
        default_rules_collection: RulesCollection,
        file: str,
        expected: int,
    ) -> None:
        """Validate that rule works as intended."""
        results = Runner(file, rules=default_rules_collection).run()

        for result in results:
            assert result.rule.id == CommandsInsteadOfModulesRule.id, result
        assert len(results) == expected
