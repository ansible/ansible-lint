"""Rule definition for usage of builtin actions only."""
import sys
from typing import Any, Dict, Optional, Union

from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule

# fqcn_builtins was added in 5.1.0 as FQCNBuiltinsRule, renamed to fqcn_builtins in 6.0.0
from ansiblelint.rules.fqcn_builtins import builtins


class OnlyBuiltinsRule(AnsibleLintRule):
    """Use only builtin actions."""

    id = "only-builtins"
    severity = "MEDIUM"
    description = "Check whether the playbook uses anything but ``ansible.builtin``"
    tags = ["opt-in", "experimental"]

    def matchtask(
        self, task: Dict[str, Any], file: Optional[Lintable] = None
    ) -> Union[bool, str]:
        fqcn_builtin = task["action"]["__ansible_module_original__"].startswith(
            "ansible.builtin."
        )
        non_fqcn_builtin = task["action"]["__ansible_module_original__"] in builtins
        return not fqcn_builtin and not non_fqcn_builtin


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:

    import pytest

    from ansiblelint.testing import RunFromText  # pylint: disable=ungrouped-imports

    SUCCESS_PLAY = """
- hosts: localhost
  tasks:
  - name: shell (fqcn)
    ansible.builtin.shell: echo This rule should not get matched by the only-builtins rule
    """

    FAIL_PLAY = """
- hosts: localhost
  tasks:
  - name: sysctl
    ansible.posix.sysctl:
      name: vm.swappiness
      value: '5'
    """

    @pytest.mark.parametrize(
        "rule_runner", (OnlyBuiltinsRule,), indirect=["rule_runner"]
    )
    def test_only_builtin_fail(rule_runner: RunFromText) -> None:
        """Test rule matches."""
        results = rule_runner.run_playbook(FAIL_PLAY)
        assert len(results) == 1
        for result in results:
            assert result.message == OnlyBuiltinsRule().shortdesc

    @pytest.mark.parametrize(
        "rule_runner", (OnlyBuiltinsRule,), indirect=["rule_runner"]
    )
    def test_only_builtin_pass(rule_runner: RunFromText) -> None:
        """Test rule does not match."""
        results = rule_runner.run_playbook(SUCCESS_PLAY)
        assert len(results) == 0, results
