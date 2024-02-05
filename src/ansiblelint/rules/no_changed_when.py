"""Implementation of the no-changed-when rule."""

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

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task


class CommandHasChangesCheckRule(AnsibleLintRule):
    """Commands should not change things if nothing needs doing."""

    id = "no-changed-when"
    severity = "HIGH"
    tags = ["command-shell", "idempotency"]
    version_added = "historic"

    _commands = [
        "ansible.builtin.command",
        "ansible.builtin.shell",
        "ansible.builtin.raw",
        "ansible.legacy.command",
        "ansible.legacy.shell",
        "ansible.legacy.raw",
        "command",
        "shell",
        "raw",
    ]

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> list[MatchError]:
        result = []
        # tasks in a block are "meta" type
        if (
            task["__ansible_action_type__"] in ["task", "meta"]
            and task["action"]["__ansible_module__"] in self._commands
            and (
                "changed_when" not in task.raw_task
                and "creates" not in task["action"]
                and "removes" not in task["action"]
            )
        ):
            result.append(self.create_matcherror(filename=file))
        return result


if "pytest" in sys.modules:
    import pytest

    # pylint: disable=ungrouped-imports
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    @pytest.mark.parametrize(
        ("file", "expected"),
        (
            pytest.param(
                "examples/playbooks/rule-no-changed-when-pass.yml",
                0,
                id="pass",
            ),
            pytest.param(
                "examples/playbooks/rule-no-changed-when-fail.yml",
                3,
                id="fail",
            ),
        ),
    )
    def test_rule_no_changed_when(
        default_rules_collection: RulesCollection,
        file: str,
        expected: int,
    ) -> None:
        """Validate no-changed-when rule."""
        results = Runner(file, rules=default_rules_collection).run()

        for result in results:
            assert result.rule.id == CommandHasChangesCheckRule.id, result
        assert len(results) == expected
