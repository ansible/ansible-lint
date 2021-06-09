"""Rule definition for usage of fully qualified collection names for builtins."""
import sys
from typing import Any, Dict, Optional, Union

from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.testing import RunFromText

builtins = [
    "add_host",
    "apt",
    "apt_key",
    "apt_repository",
    "assemble",
    "assert",
    "async_status",
    "blockinfile",
    "command",
    "copy",
    "cron",
    "debconf",
    "debug",
    "dnf",
    "dpkg_selections",
    "expect",
    "fail",
    "fetch",
    "file",
    "find",
    "gather_facts",
    "get_url",
    "getent",
    "git",
    "group",
    "group_by",
    "hostname",
    "import_playbook",
    "import_role",
    "import_tasks",
    "include",
    "include_role",
    "include_tasks",
    "include_vars",
    "iptables",
    "known_hosts",
    "lineinfile",
    "meta",
    "package",
    "package_facts",
    "pause",
    "ping",
    "pip",
    "raw",
    "reboot",
    "replace",
    "rpm_key",
    "script",
    "service",
    "service_facts",
    "set_fact",
    "set_stats",
    "setup",
    "shell",
    "slurp",
    "stat",
    "subversion",
    "systemd",
    "sysvinit",
    "tempfile",
    "template",
    "unarchive",
    "uri",
    "user",
    "wait_for",
    "wait_for_connection",
    "yum",
    "yum_repository",
]


class FQCNBuiltinsRule(AnsibleLintRule):
    id = "fqcn-builtins"
    shortdesc = "Use FQCN for builtin actions"
    description = (
        'Check whether the long version starting with ``ansible.builtin`` '
        'is used in the playbook'
    )
    tags = ["opt-in", "formatting", "experimental"]

    def matchtask(
        self, task: Dict[str, Any], file: Optional[Lintable] = None
    ) -> Union[bool, str]:
        return task["action"]["__ansible_module_original__"] in builtins


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:

    import pytest

    SUCCESS_PLAY = '''
- hosts: localhost
  tasks:
  - name: shell (fqcn)
    ansible.builtin.shell: echo This rule should not get matched by the fqcn-builtins rule
    '''

    FAIL_PLAY = '''
- hosts: localhost
  tasks:
  - name: shell (fqcn)
    shell: echo This rule should get matched by the fqcn-builtins rule
    '''

    @pytest.mark.parametrize(
        'rule_runner', (FQCNBuiltinsRule,), indirect=['rule_runner']
    )
    def test_fqcn_builtin_fail(rule_runner: RunFromText) -> None:
        """Test rule matches."""
        results = rule_runner.run_playbook(FAIL_PLAY)
        assert len(results) == 1
        for result in results:
            assert result.message == FQCNBuiltinsRule.shortdesc

    @pytest.mark.parametrize(
        'rule_runner', (FQCNBuiltinsRule,), indirect=['rule_runner']
    )
    def test_fqcn_builtin_pass(rule_runner: RunFromText) -> None:
        """Test rule does not match."""
        results = rule_runner.run_playbook(SUCCESS_PLAY)
        assert len(results) == 0, results
