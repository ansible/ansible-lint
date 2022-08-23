"""Implementation of NameRule."""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from ansiblelint.errors import MatchError
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.utils import LINE_NUMBER_KEY

if TYPE_CHECKING:
    from typing import Optional

    from ansiblelint.constants import odict
    from ansiblelint.file_utils import Lintable


class NameRule(AnsibleLintRule):
    """Rule for checking task and play names."""

    id = "name"
    description = (
        "All tasks and plays should have a distinct name for readability "
        "and for ``--start-at-task`` to work"
    )
    severity = "MEDIUM"
    tags = ["idiom"]
    version_added = "v6.5.0 (last update)"

    def matchplay(self, file: Lintable, data: odict[str, Any]) -> list[MatchError]:
        """Return matches found for a specific play (entry in playbook)."""
        if file.kind != "playbook":
            return []
        if "name" not in data and not any(
            key in data
            for key in ["import_playbook", "ansible.builtin.import_playbook"]
        ):
            return [
                self.create_matcherror(
                    message="All plays should be named.",
                    linenumber=data[LINE_NUMBER_KEY],
                    tag="name[play]",
                    filename=file,
                )
            ]
        match = self._check_name(
            data["name"], lintable=file, linenumber=data[LINE_NUMBER_KEY]
        )
        if match:
            return [match]
        return []

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> bool | str | MatchError:
        name = task.get("name")
        if not name:
            return self.create_matcherror(
                message="All tasks should be named.",
                linenumber=task[LINE_NUMBER_KEY],
                tag="name[missing]",
                filename=file,
            )
        return (
            self._check_name(name, lintable=file, linenumber=task[LINE_NUMBER_KEY])
            or False
        )

    def _check_name(
        self, name: str, lintable: Lintable | None, linenumber: int
    ) -> MatchError | None:
        if not name[0].isupper():
            return self.create_matcherror(
                message="All names should start with an uppercase letter.",
                linenumber=linenumber,
                tag="name[casing]",
                filename=lintable,
            )
        return None


if "pytest" in sys.modules:  # noqa: C901

    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    def test_file_positive() -> None:
        """Positive test for unnamed-task."""
        collection = RulesCollection()
        collection.register(NameRule())
        success = "examples/playbooks/task-has-name-success.yml"
        good_runner = Runner(success, rules=collection)
        assert [] == good_runner.run()

    def test_file_negative() -> None:
        """Negative test for unnamed-task."""
        collection = RulesCollection()
        collection.register(NameRule())
        failure = "examples/playbooks/task-has-name-failure.yml"
        bad_runner = Runner(failure, rules=collection)
        errs = bad_runner.run()
        assert len(errs) == 5

    def test_rule_name_lowercase() -> None:
        """Negative test for a task that starts with lowercase."""
        collection = RulesCollection()
        collection.register(NameRule())
        failure = "examples/playbooks/task-name-lowercase.yml"
        bad_runner = Runner(failure, rules=collection)
        errs = bad_runner.run()
        assert len(errs) == 1
        assert errs[0].tag == "name[casing]"
        assert errs[0].rule.id == "name"

    def test_name_play() -> None:
        """Positive test for name[play]."""
        collection = RulesCollection()
        collection.register(NameRule())
        success = "examples/playbooks/play-name-missing.yml"
        errs = Runner(success, rules=collection).run()
        assert len(errs) == 1
        assert errs[0].tag == "name[play]"
        assert errs[0].rule.id == "name"
