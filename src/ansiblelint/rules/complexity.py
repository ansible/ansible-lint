"""Implementation of limiting number of tasks."""
from __future__ import annotations

import re
import sys
from typing import TYPE_CHECKING, Any

from ansiblelint.config import options
from ansiblelint.constants import LINE_NUMBER_KEY
from ansiblelint.errors import MatchError
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable  # noqa: F811


class ComplexityRule(AnsibleLintRule):
    """Rule for limiting number of tasks inside a file."""

    id = "complexity"
    description = "There should be limited tasks executed inside any file"
    severity = "MEDIUM"
    tags = ["experimental", "idiom"]
    version_added = "v6.15.0 (last update)"
    _re_templated_inside = re.compile(r".*\{\{.*\}\}.*\w.*$")

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        """Call matchplay for up to no_of_max_tasks inside file and return aggregate results."""
        results: list[MatchError] = []

        if file.kind != "playbook":
            return []
        if len(data["tasks"]) > options.max_tasks:
            results.append(
                self.create_matcherror(
                    message=f"Maximum tasks allowed in a play is {options.max_tasks}.",
                    linenumber=data[LINE_NUMBER_KEY],
                    tag="complexity[play]",
                    filename=file,
                ),
            )
        return results


if "pytest" in sys.modules:  # noqa: C901
    import pytest

    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.runner import Runner  # pylint: disable=ungrouped-imports

    @pytest.mark.parametrize(
        ("file", "expected"),
        (
            pytest.param(
                "examples/playbooks/rule-complexity-pass.yml",
                0,
                id="pass",
            ),
            pytest.param(
                "examples/playbooks/rule-complexity-fail.yml",
                1,
                id="fail",
            ),
        ),
    )
    def test_complexity(
        default_rules_collection: RulesCollection,
        file: str,
        expected: int,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test rule."""
        monkeypatch.setattr(options, "max_tasks", 5)
        collection = RulesCollection()
        collection.register(ComplexityRule())
        results = Runner(file, rules=default_rules_collection).run()

        for result in results:
            assert result.rule.id == ComplexityRule.id, result
            assert result.tag == "complexity[play]"
        assert len(results) == expected
