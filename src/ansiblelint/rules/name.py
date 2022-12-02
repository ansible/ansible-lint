"""Implementation of NameRule."""
from __future__ import annotations

import re
import sys
from copy import deepcopy
from typing import TYPE_CHECKING, Any

from ansiblelint.constants import LINE_NUMBER_KEY
from ansiblelint.errors import MatchError
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable  # noqa: F811


class NameRule(AnsibleLintRule):
    """Rule for checking task and play names."""

    id = "name"
    description = (
        "All tasks and plays should have a distinct name for readability "
        "and for ``--start-at-task`` to work"
    )
    severity = "MEDIUM"
    tags = ["idiom"]
    version_added = "v6.9.1 (last update)"
    _re_templated_inside = re.compile(r".*\{\{.*\}\}(.+)$")

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        """Return matches found for a specific play (entry in playbook)."""
        results = []
        if file.kind != "playbook":
            return []
        if "name" not in data:
            return [
                self.create_matcherror(
                    message="All plays should be named.",
                    linenumber=data[LINE_NUMBER_KEY],
                    tag="name[play]",
                    filename=file,
                )
            ]
        results.extend(
            self._check_name(
                data["name"], lintable=file, linenumber=data[LINE_NUMBER_KEY]
            )
        )
        return results

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> list[MatchError]:
        results = []
        name = task.get("name")
        if not name:
            results.append(
                self.create_matcherror(
                    message="All tasks should be named.",
                    linenumber=task[LINE_NUMBER_KEY],
                    tag="name[missing]",
                    filename=file,
                )
            )
        else:
            results.extend(
                self._prefix_check(
                    name, lintable=file, linenumber=task[LINE_NUMBER_KEY]
                )
            )
            task_name = name.split("|")
            if len(task_name) > 1:
                name = task_name[1].strip()
            results.extend(
                self._check_name(name, lintable=file, linenumber=task[LINE_NUMBER_KEY])
            )
        return results

    def _prefix_check(
        self, name: str, lintable: Lintable | None, linenumber: int
    ) -> list[MatchError]:

        results: list[MatchError] = []
        if lintable is None:
            return []

        if self._collection:
            prefix = self._collection.options.task_name_prefix.format(
                stem=lintable.path.stem
            )
            if (
                lintable.kind == "tasks"
                and lintable.path.stem != "main"
                and not name.startswith(prefix)
            ):
                # For the moment in order to raise errors this rule needs to be
                # enabled manually. Still, we do allow use of prefixes even without
                # having to enable the rule.
                if "name[prefix]" in self._collection.options.enable_list:
                    results.append(
                        self.create_matcherror(
                            message=f"Task name should start with '{prefix}'.",
                            linenumber=linenumber,
                            tag="name[prefix]",
                            filename=lintable,
                        )
                    )
        return results

    def _check_name(
        self, name: str, lintable: Lintable | None, linenumber: int
    ) -> list[MatchError]:
        # This rules applies only to languages that do have uppercase and
        # lowercase letter, so we ignore anything else. On Unicode isupper()
        # is not necessarily the opposite of islower()
        results = []
        if name[0].isalpha() and name[0].islower() and not name[0].isupper():
            results.append(
                self.create_matcherror(
                    message="All names should start with an uppercase letter.",
                    linenumber=linenumber,
                    tag="name[casing]",
                    filename=lintable,
                )
            )
        if self._re_templated_inside.match(name):
            results.append(
                self.create_matcherror(
                    message="Jinja templates should only be at the end of 'name'",
                    linenumber=linenumber,
                    tag="name[template]",
                    filename=lintable,
                )
            )
        return results


if "pytest" in sys.modules:  # noqa: C901

    from ansiblelint.config import options
    from ansiblelint.file_utils import Lintable  # noqa: F811
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    def test_file_positive() -> None:
        """Positive test for unnamed-task."""
        collection = RulesCollection()
        collection.register(NameRule())
        success = "examples/playbooks/rule-name-missing-pass.yml"
        good_runner = Runner(success, rules=collection)
        assert [] == good_runner.run()

    def test_file_negative() -> None:
        """Negative test for unnamed-task."""
        collection = RulesCollection()
        collection.register(NameRule())
        failure = "examples/playbooks/rule-name-missing-fail.yml"
        bad_runner = Runner(failure, rules=collection)
        errs = bad_runner.run()
        assert len(errs) == 5

    def test_name_prefix_negative() -> None:
        """Negative test for unnamed-task."""
        custom_options = deepcopy(options)
        custom_options.enable_list = ["name[prefix]"]
        collection = RulesCollection(options=custom_options)
        collection.register(NameRule())
        failure = Lintable(
            "examples/playbooks/tasks/rule-name-prefix-fail.yml", kind="tasks"
        )
        bad_runner = Runner(failure, rules=collection)
        results = bad_runner.run()
        assert len(results) == 3
        assert results[0].tag == "name[casing]"
        assert results[1].tag == "name[prefix]"
        assert results[2].tag == "name[prefix]"

    def test_rule_name_lowercase() -> None:
        """Negative test for a task that starts with lowercase."""
        collection = RulesCollection()
        collection.register(NameRule())
        failure = "examples/playbooks/rule-name-casing.yml"
        bad_runner = Runner(failure, rules=collection)
        errs = bad_runner.run()
        assert len(errs) == 1
        assert errs[0].tag == "name[casing]"
        assert errs[0].rule.id == "name"

    def test_name_play() -> None:
        """Positive test for name[play]."""
        collection = RulesCollection()
        collection.register(NameRule())
        success = "examples/playbooks/rule-name-play-fail.yml"
        errs = Runner(success, rules=collection).run()
        assert len(errs) == 1
        assert errs[0].tag == "name[play]"
        assert errs[0].rule.id == "name"

    def test_name_template() -> None:
        """Negative test for name[templated]."""
        collection = RulesCollection()
        collection.register(NameRule())
        failure = "examples/playbooks/rule-name-templated-fail.yml"
        bad_runner = Runner(failure, rules=collection)
        errs = bad_runner.run()
        assert len(errs) == 1
        assert errs[0].tag == "name[template]"
