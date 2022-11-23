"""Rule definition for usage of builtin actions only."""
from __future__ import annotations

import sys
from typing import Any

from ansiblelint.config import options
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule

# fqcn_builtins was added in 5.1.0 as FQCNBuiltinsRule, renamed to fqcn_builtins in 6.0.0
from ansiblelint.rules.fqcn import builtins
from ansiblelint.skip_utils import is_nested_task


class OnlyBuiltinsRule(AnsibleLintRule):
    """Use only builtin actions."""

    id = "only-builtins"
    severity = "MEDIUM"
    description = "Check whether the playbook uses anything but ``ansible.builtin``"
    tags = ["opt-in", "experimental"]

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> bool | str:
        module = task["action"]["__ansible_module_original__"]

        is_builtin = module.startswith("ansible.builtin.") or module in builtins

        is_manually_allowed = any(
            module.startswith(f"{prefix}.")
            for prefix in options.only_builtins_allow_collections
        )

        return not is_builtin and not is_manually_allowed and not is_nested_task(task)


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:

    # pylint: disable=ungrouped-imports
    import pytest

    from ansiblelint.constants import SUCCESS_RC, VIOLATIONS_FOUND_RC
    from ansiblelint.testing import RunFromText, run_ansible_lint

    SUCCESS_PLAY = """
- hosts: localhost
  tasks:
  - name: A block
    block:
    - name: Shell (fqcn)
      ansible.builtin.shell: echo This rule should not get matched by the only-builtins rule
    """

    def test_only_builtins_fail() -> None:
        """Test rule matches."""
        result = run_ansible_lint(
            "--strict",
            "--warn-list=",
            "--enable-list",
            "only-builtins",
            "examples/playbooks/rule-only-builtins.yml",
        )
        assert result.returncode == VIOLATIONS_FOUND_RC
        assert "Failed" in result.stderr
        assert "1 warning(s)" in result.stderr
        assert "only-builtins: Use only builtin actions" in result.stdout

    def test_only_builtins_allow_collections() -> None:
        """Test rule doesn't match."""
        conf_path = "examples/playbooks/.ansible-lint-only-builtins-allow-collections"
        result = run_ansible_lint(
            f"--config-file={conf_path}",
            "--strict",
            "--warn-list=",
            "--enable-list",
            "only-builtins",
            "examples/playbooks/rule-only-builtins.yml",
        )
        assert "only-builtins" not in result.stdout
        assert result.returncode == SUCCESS_RC

    @pytest.mark.parametrize(
        "rule_runner", (OnlyBuiltinsRule,), indirect=["rule_runner"]
    )
    def test_only_builtin_pass(rule_runner: RunFromText) -> None:
        """Test rule does not match."""
        results = rule_runner.run_playbook(SUCCESS_PLAY)
        assert len(results) == 0, results
