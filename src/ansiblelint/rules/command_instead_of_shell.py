"""Implementation of command-instead-of-shell rule."""

# Copyright (c) 2016 Will Thames <will@thames.id.au>
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
from typing import TYPE_CHECKING

from ansiblelint.rules import AnsibleLintRule, TransformMixin
from ansiblelint.utils import get_cmd_args

if TYPE_CHECKING:
    from ruamel.yaml.comments import CommentedMap, CommentedSeq

    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task


class UseCommandInsteadOfShellRule(AnsibleLintRule, TransformMixin):
    """Use shell only when shell functionality is required."""

    id = "command-instead-of-shell"
    description = (
        "Shell should only be used when piping, redirecting "
        "or chaining commands (and Ansible would be preferred "
        "for some of those!)"
    )
    severity = "HIGH"
    tags = ["command-shell", "idiom"]
    version_added = "historic"

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> bool | str:
        # Use unjinja so that we don't match on jinja filters
        # rather than pipes
        if task["action"]["__ansible_module__"] in ["shell", "ansible.builtin.shell"]:
            # Since Ansible 2.4, the `command` module does not accept setting
            # the `executable`. If the user needs to set it, they have to use
            # the `shell` module.
            if "executable" in task["action"]:
                return False

            jinja_stripped_cmd = self.unjinja(get_cmd_args(task))
            return not any(ch in jinja_stripped_cmd for ch in "&|<>;$\n*[]{}?`")
        return False

    def transform(
        self,
        match: MatchError,
        lintable: Lintable,
        data: CommentedMap | CommentedSeq | str,
    ) -> None:
        if match.tag == "command-instead-of-shell":
            target_task = self.seek(match.yaml_path, data)
            for _ in range(len(target_task)):
                k, v = target_task.popitem(False)
                target_task["ansible.builtin.command" if "shell" in k else k] = v
            match.fixed = True


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    import pytest

    # pylint: disable=ungrouped-imports
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    @pytest.mark.parametrize(
        ("file", "expected"),
        (
            pytest.param(
                "examples/playbooks/rule-command-instead-of-shell-pass.yml",
                0,
                id="good",
            ),
            pytest.param(
                "examples/playbooks/rule-command-instead-of-shell-fail.yml",
                3,
                id="bad",
            ),
        ),
    )
    def test_rule_command_instead_of_shell(
        default_rules_collection: RulesCollection,
        file: str,
        expected: int,
    ) -> None:
        """Validate that rule works as intended."""
        results = Runner(file, rules=default_rules_collection).run()
        for result in results:
            assert result.rule.id == UseCommandInsteadOfShellRule.id, result
        assert len(results) == expected
