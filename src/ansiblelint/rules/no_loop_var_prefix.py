"""Optional Ansible-lint rule to enforce use of prefix on role loop vars."""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, Dict, Union

from ansiblelint.config import options
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.text import toidentifier

if TYPE_CHECKING:
    from typing import Optional

    from ansiblelint.file_utils import Lintable


class RoleLoopVarPrefix(AnsibleLintRule):
    """Role loop_var should use configured prefix."""

    id = "no-loop-var-prefix"
    link = (
        "https://docs.ansible.com/ansible/latest/user_guide/"
        "playbooks_loops.html#defining-inner-and-outer-variable-names-with-loop-var"
    )
    description = """\
Looping inside roles has the risk of clashing with loops from user-playbooks.\
"""

    tags = ["idiom"]
    prefix = ""
    severity = "MEDIUM"

    def matchtask(
        self, task: Dict[str, Any], file: Optional[Lintable] = None
    ) -> Union[bool, str]:
        """Return matches for a task."""
        if not file or not file.role or not options.loop_var_prefix:
            return False

        self.prefix = options.loop_var_prefix.format(role=toidentifier(file.role))

        has_loop = "loop" in task
        for key in task.keys():
            if key.startswith("with_"):
                has_loop = True

        if has_loop:
            loop_control = task.get("loop_control", {})
            loop_var = loop_control.get("loop_var", "")

            if not loop_var or not loop_var.startswith(self.prefix):
                return True

        return False


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:

    import pytest

    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.runner import Runner  # pylint: disable=ungrouped-imports

    @pytest.mark.parametrize(
        ("test_file", "failures"),
        (
            pytest.param(
                "examples/playbooks/roles/loop_var_prefix/tasks/pass.yml", 0, id="pass"
            ),
            pytest.param(
                "examples/playbooks/roles/loop_var_prefix/tasks/fail.yml", 5, id="fail"
            ),
        ),
    )
    def test_no_loop_var_prefix(
        default_rules_collection: RulesCollection, test_file: str, failures: int
    ) -> None:
        """Test rule matches."""
        # Enable checking of loop variable prefixes in roles
        options.loop_var_prefix = "{role}_"
        results = Runner(test_file, rules=default_rules_collection).run()
        assert len(results) == failures
        for result in results:
            assert result.message == RoleLoopVarPrefix().shortdesc
