"""Optional Ansible-lint rule to enforce use of prefix on role loop vars."""

from __future__ import annotations

import re
import sys
from typing import TYPE_CHECKING

from ansiblelint.config import LOOP_VAR_PREFIX, options
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.text import toidentifier

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task


class RoleLoopVarPrefix(AnsibleLintRule):
    """Role loop_var should use configured prefix."""

    id = "loop-var-prefix"
    link = (
        "https://docs.ansible.com/ansible/latest/playbook_guide/"
        "playbooks_loops.html#defining-inner-and-outer-variable-names-with-loop-var"
    )
    description = """\
Looping inside roles has the risk of clashing with loops from user-playbooks.\
"""

    tags = ["idiom"]
    prefix = re.compile("")
    severity = "MEDIUM"
    _ids = {
        "loop-var-prefix[wrong]": "Loop variable name does not match regex.",
        "loop-var-prefix[missing]": "Replace unsafe implicit `item` loop variable.",
    }

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> list[MatchError]:
        """Return matches for a task."""
        if not file or not file.role or not options.loop_var_prefix:
            return []

        self.prefix = re.compile(
            options.loop_var_prefix.format(role=toidentifier(file.role)),
        )
        has_loop = "loop" in task.raw_task
        for key in task.raw_task:
            if key.startswith("with_"):
                has_loop = True

        if has_loop:
            loop_control = task.raw_task.get("loop_control", {})
            loop_var = loop_control.get("loop_var", "")

            if loop_var:
                if not self.prefix.match(loop_var):
                    return [
                        self.create_matcherror(
                            message=f"Loop variable name does not match /{options.loop_var_prefix}/ regex, where role={toidentifier(file.role)}.",
                            filename=file,
                            tag="loop-var-prefix[wrong]",
                        ),
                    ]
            else:
                return [
                    self.create_matcherror(
                        message=f"Replace unsafe implicit `item` loop variable by adding a `loop_var` that is matching /{options.loop_var_prefix}/ regex.",
                        filename=file,
                        tag="loop-var-prefix[missing]",
                    ),
                ]

        return []


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    import pytest

    # pylint: disable=ungrouped-imports
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    @pytest.mark.parametrize(
        ("test_file", "failures"),
        (
            pytest.param(
                "examples/playbooks/roles/loop_var_prefix/tasks/pass.yml",
                0,
                id="pass",
            ),
            pytest.param(
                "examples/playbooks/roles/loop_var_prefix/tasks/fail.yml",
                6,
                id="fail",
            ),
        ),
    )
    def test_loop_var_prefix(
        default_rules_collection: RulesCollection,
        test_file: str,
        failures: int,
    ) -> None:
        """Test rule matches."""
        # Enable checking of loop variable prefixes in roles
        options.loop_var_prefix = LOOP_VAR_PREFIX
        results = Runner(test_file, rules=default_rules_collection).run()
        for result in results:
            assert result.rule.id == RoleLoopVarPrefix().id
        assert len(results) == failures
