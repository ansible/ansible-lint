# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
"""command-instead-of-module rule testing."""
import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.CommandsInsteadOfModulesRule import CommandsInsteadOfModulesRule
from ansiblelint.testing import RunFromText

APT_GET = '''\
- name: run apt-get update
  command: apt-get update
'''

GIT_BRANCH = '''\
- name: print current git branch
  command: git branch
'''

GIT_LOG = '''\
- name: print git log
  command: git log
'''

RESTART_SSHD = '''\
- name: restart sshd
  command: systemctl restart sshd
'''

SYSTEMD_ENVIRONMENT = '''\
- name: show systemd environment
  command: systemctl show-environment
'''

SYSTEMD_RUNLEVEL = '''\
- name: set systemd runlevel
  command: systemctl set-default multi-user.target
'''


class TestCommandsInsteadOfModulesRule(unittest.TestCase):
    """Unit test for command-instead-of-module rule."""

    collection = RulesCollection()
    collection.register(CommandsInsteadOfModulesRule())

    def setUp(self):
        """Set up a runner."""
        self.runner = RunFromText(self.collection)

    def test_apt_get(self):
        """The apt module supports update."""
        results = self.runner.run_role_tasks_main(APT_GET)
        assert len(results) == 1

    def test_git_branch(self):
        """The git branch command is not supported by the git module."""
        results = self.runner.run_role_tasks_main(GIT_BRANCH)
        assert len(results) == 0

    def test_git_log(self):
        """The git log command is not supported by the git module."""
        results = self.runner.run_role_tasks_main(GIT_LOG)
        assert len(results) == 0

    def test_restart_sshd(self):
        """Restarting services is supported by the systemd module."""
        results = self.runner.run_role_tasks_main(RESTART_SSHD)
        assert len(results) == 1

    def test_systemd_environment(self):
        """Showing the environment is not supported by the systemd module."""
        results = self.runner.run_role_tasks_main(SYSTEMD_ENVIRONMENT)
        assert len(results) == 0

    def test_systemd_runlevel(self):
        """Set-default is not supported by the systemd module."""
        results = self.runner.run_role_tasks_main(SYSTEMD_RUNLEVEL)
        assert len(results) == 0
