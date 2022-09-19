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

import os
import sys
from typing import TYPE_CHECKING, Any

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.utils import convert_to_boolean, get_first_cmd_arg, get_second_cmd_arg

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable


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
        "git": ["branch", "log", "lfs"],
        "systemctl": ["--version", "set-default", "show-environment", "status"],
        "yum": ["clean"],
        "rpm": ["--nodeps"],
    }

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> bool | str:

        if task["action"]["__ansible_module__"] not in self._commands:
            return False

        first_cmd_arg = get_first_cmd_arg(task)
        second_cmd_arg = get_second_cmd_arg(task)

        if not first_cmd_arg:
            return False

        executable = os.path.basename(first_cmd_arg)

        if (
            second_cmd_arg
            and executable in self._executable_options
            and second_cmd_arg in self._executable_options[executable]
        ):
            return False

        if executable in self._modules and convert_to_boolean(
            task["action"].get("warn", True)
        ):
            message = "{0} used in place of {1} module"
            return message.format(executable, self._modules[executable])
        return False


if "pytest" in sys.modules:  # noqa: C901
    import pytest

    from ansiblelint.testing import RunFromText  # pylint: disable=ungrouped-imports

    APT_GET = """
- hosts: all
  tasks:
    - name: Run apt-get update
      command: apt-get update
"""

    GIT_COMMANDS_OK = """
- hosts: all
  tasks:
    - name: Print current git branch
      command: git branch
    - name: Print git log
      command: git log
    - name: Install git lfs support
      command: git lfs install
"""

    RESTART_SSHD = """
- hosts: all
  tasks:
    - name: Restart sshd
      command: systemctl restart sshd
"""

    SYSTEMCTL_STATUS = """
- hosts: all
  tasks:
    - name: Show systemctl service status
      command: systemctl status systemd-timesyncd
"""

    SYSTEMD_ENVIRONMENT = """
- hosts: all
  tasks:
    - name: Show systemd environment
      command: systemctl show-environment
"""

    SYSTEMD_RUNLEVEL = """
- hosts: all
  tasks:
    - name: Set systemd runlevel
      command: systemctl set-default multi-user.target
"""

    YUM_UPDATE = """
- hosts: all
  tasks:
    - name: Run yum update
      command: yum update
"""

    YUM_CLEAN = """
- hosts: all
  tasks:
    - name: Clear yum cache
      command: yum clean all
"""

    @pytest.mark.parametrize(
        "rule_runner", (CommandsInsteadOfModulesRule,), indirect=["rule_runner"]
    )
    def test_apt_get(rule_runner: RunFromText) -> None:
        """The apt module supports update."""
        results = rule_runner.run_playbook(APT_GET)
        assert len(results) == 1

    @pytest.mark.parametrize(
        "rule_runner", (CommandsInsteadOfModulesRule,), indirect=["rule_runner"]
    )
    def test_restart_sshd(rule_runner: RunFromText) -> None:
        """Restarting services is supported by the systemd module."""
        results = rule_runner.run_playbook(RESTART_SSHD)
        assert len(results) == 1

    @pytest.mark.parametrize(
        "rule_runner", (CommandsInsteadOfModulesRule,), indirect=["rule_runner"]
    )
    def test_git_commands_ok(rule_runner: RunFromText) -> None:
        """Check the git commands not supported by the git module do not trigger rule."""
        results = rule_runner.run_playbook(GIT_COMMANDS_OK)
        assert len(results) == 0

    @pytest.mark.parametrize(
        "rule_runner", (CommandsInsteadOfModulesRule,), indirect=["rule_runner"]
    )
    def test_systemd_status(rule_runner: RunFromText) -> None:
        """Set-default is not supported by the systemd module."""
        results = rule_runner.run_playbook(SYSTEMCTL_STATUS)
        assert len(results) == 0

    @pytest.mark.parametrize(
        "rule_runner", (CommandsInsteadOfModulesRule,), indirect=["rule_runner"]
    )
    def test_systemd_environment(rule_runner: RunFromText) -> None:
        """Showing the environment is not supported by the systemd module."""
        results = rule_runner.run_playbook(SYSTEMD_ENVIRONMENT)
        assert len(results) == 0

    @pytest.mark.parametrize(
        "rule_runner", (CommandsInsteadOfModulesRule,), indirect=["rule_runner"]
    )
    def test_systemd_runlevel(rule_runner: RunFromText) -> None:
        """Set-default is not supported by the systemd module."""
        results = rule_runner.run_playbook(SYSTEMD_RUNLEVEL)
        assert len(results) == 0

    @pytest.mark.parametrize(
        "rule_runner", (CommandsInsteadOfModulesRule,), indirect=["rule_runner"]
    )
    def test_yum_update(rule_runner: RunFromText) -> None:
        """Using yum update should fail."""
        results = rule_runner.run_playbook(YUM_UPDATE)
        assert len(results) == 1

    @pytest.mark.parametrize(
        "rule_runner", (CommandsInsteadOfModulesRule,), indirect=["rule_runner"]
    )
    def test_yum_clean(rule_runner: RunFromText) -> None:
        """The yum module does not support clearing yum cache."""
        results = rule_runner.run_playbook(YUM_CLEAN)
        assert len(results) == 0
