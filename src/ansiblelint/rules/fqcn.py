"""Rule definition for usage of fully qualified collection names for builtins."""
from __future__ import annotations

import sys
from typing import Any

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule

builtins = [
    # spell-checker:disable
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
    # spell-checker:enable
]


class FQCNBuiltinsRule(AnsibleLintRule):
    """Use FQCN for builtin actions."""

    id = "fqcn"
    severity = "MEDIUM"
    description = (
        "Check whether actions are using using full qualified collection names."
    )
    tags = ["formatting"]
    version_added = "v6.8.0"

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> list[MatchError]:
        result = []
        module = task["action"]["__ansible_module_original__"]
        if module in builtins:
            result.append(
                self.create_matcherror(
                    message=f"Use FQCN for builtin module actions ({module}).",
                    details=f"Use `ansible.builtin.{module}` or `ansible.legacy.{module}` instead.",
                    filename=file,
                    linenumber=task["__line__"],
                    tag="fqcn[action-core]",
                )
            )
        # Add here implementation for fqcn[action-redirect]
        elif module != "block/always/rescue" and module.count(".") < 2:
            result.append(
                self.create_matcherror(
                    message=f"Use FQCN for module actions, such `<namespace>.<collection>.{module}`.",
                    details=f"Action `{module}` is not FQCN.",
                    filename=file,
                    linenumber=task["__line__"],
                    tag="fqcn[action]",
                )
            )
        return result


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:

    import pytest

    from ansiblelint.testing import RunFromText  # pylint: disable=ungrouped-imports

    SUCCESS_PLAY = """
- hosts: localhost
  tasks:
  - name: Shell (fqcn)
    ansible.builtin.shell: echo This rule should not get matched by the fqcn rule
  - name: Use FQCN with more than 3 parts
    community.general.system.sudoers:
      name: should-not-be-here
      state: absent
    """

    FAIL_PLAY = """
- hosts: localhost
  tasks:
  - name: Shell (fqcn[action-core])
    shell: echo This rule should get matched by the fqcn rule
  - name: Shell (fqcn[action])
    ini_file:
        path: /tmp/test.ini
    """

    @pytest.mark.parametrize(
        "rule_runner", (FQCNBuiltinsRule,), indirect=["rule_runner"]
    )
    def test_fqcn_builtin_fail(rule_runner: RunFromText) -> None:
        """Test rule matches."""
        results = rule_runner.run_playbook(FAIL_PLAY)
        assert len(results) == 2
        assert results[0].tag == "fqcn[action-core]"
        assert "Use FQCN for builtin module actions" in results[0].message
        assert results[1].tag == "fqcn[action]"
        assert (
            "Use FQCN for module actions, such `<namespace>.<collection>"
            in results[1].message
        )

    @pytest.mark.parametrize(
        "rule_runner", (FQCNBuiltinsRule,), indirect=["rule_runner"]
    )
    def test_fqcn_builtin_pass(rule_runner: RunFromText) -> None:
        """Test rule does not match."""
        results = rule_runner.run_playbook(SUCCESS_PLAY)
        assert len(results) == 0, results
