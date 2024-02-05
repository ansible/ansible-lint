"""Implementation of risky-shell-pipe rule."""

from __future__ import annotations

import re
import sys
from typing import TYPE_CHECKING

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.utils import convert_to_boolean, get_cmd_args

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task


class ShellWithoutPipefail(AnsibleLintRule):
    """Shells that use pipes should set the pipefail option."""

    id = "risky-shell-pipe"
    description = (
        "Without the pipefail option set, a shell command that "
        "implements a pipeline can fail and still return 0. If "
        "any part of the pipeline other than the terminal command "
        "fails, the whole pipeline will still return 0, which may "
        "be considered a success by Ansible. "
        "Pipefail is available in the bash shell."
    )
    severity = "MEDIUM"
    tags = ["command-shell"]
    version_added = "v4.1.0"

    _pipefail_re = re.compile(r"^\s*set.*[+-][A-Za-z]*o\s*pipefail", re.M)
    _pipe_re = re.compile(r"(?<!\|)\|(?!\|)")

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> bool | str:
        if task["__ansible_action_type__"] != "task":
            return False

        if task["action"]["__ansible_module__"] != "shell":
            return False

        if task.get("ignore_errors"):
            return False

        jinja_stripped_cmd = self.unjinja(get_cmd_args(task))

        # https://github.com/ansible/ansible-lint/issues/3161
        if "pwsh" in task["action"].get("executable", ""):
            return False

        return bool(
            self._pipe_re.search(jinja_stripped_cmd)
            and not self._pipefail_re.search(jinja_stripped_cmd)
            and not convert_to_boolean(task["action"].get("ignore_errors", False)),
        )


if "pytest" in sys.modules:
    import pytest

    # pylint: disable=ungrouped-imports
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    @pytest.mark.parametrize(
        ("file", "expected"),
        (
            pytest.param(
                "examples/playbooks/rule-risky-shell-pipe-pass.yml",
                0,
                id="pass",
            ),
            pytest.param(
                "examples/playbooks/rule-risky-shell-pipe-fail.yml",
                3,
                id="fail",
            ),
        ),
    )
    def test_risky_shell_pipe(
        default_rules_collection: RulesCollection,
        file: str,
        expected: int,
    ) -> None:
        """Validate that rule works as intended."""
        results = Runner(file, rules=default_rules_collection).run()

        for result in results:
            assert result.rule.id == ShellWithoutPipefail.id, result
        assert len(results) == expected
