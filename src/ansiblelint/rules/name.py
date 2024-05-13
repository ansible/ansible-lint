"""Implementation of NameRule."""

from __future__ import annotations

import re
import sys
from typing import TYPE_CHECKING, Any

import wcmatch.pathlib
import wcmatch.wcmatch

from ansiblelint.constants import LINE_NUMBER_KEY
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule, TransformMixin

if TYPE_CHECKING:
    from ruamel.yaml.comments import CommentedMap, CommentedSeq

    from ansiblelint.config import Options
    from ansiblelint.errors import MatchError
    from ansiblelint.utils import Task


class NameRule(AnsibleLintRule, TransformMixin):
    """Rule for checking task and play names."""

    id = "name"
    description = (
        "All tasks and plays should have a distinct name for readability "
        "and for ``--start-at-task`` to work"
    )
    severity = "MEDIUM"
    tags = ["idiom"]
    version_added = "v6.9.1 (last update)"
    _re_templated_inside = re.compile(r".*\{\{.*\}\}.*\w.*$")
    _ids = {
        "name[play]": "All plays should be named.",
        "name[missing]": "All tasks should be named.",
        "name[prefix]": "Task name should start with a prefix.",
        "name[casing]": "All names should start with an uppercase letter.",
        "name[template]": "Jinja templates should only be at the end of 'name'",
    }

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        """Return matches found for a specific play (entry in playbook)."""
        results: list[MatchError] = []
        if file.kind != "playbook":
            return []
        if file.failed():
            return results
        if "name" not in data:
            return [
                self.create_matcherror(
                    message="All plays should be named.",
                    lineno=data[LINE_NUMBER_KEY],
                    tag="name[play]",
                    filename=file,
                ),
            ]
        results.extend(
            self._check_name(
                data["name"],
                lintable=file,
                lineno=data[LINE_NUMBER_KEY],
            ),
        )
        return results

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> list[MatchError]:
        results: list[MatchError] = []
        if file and file.failed():
            return results
        name = task.get("name")
        if not name:
            results.append(
                self.create_matcherror(
                    message="All tasks should be named.",
                    lineno=task[LINE_NUMBER_KEY],
                    tag="name[missing]",
                    filename=file,
                ),
            )
        else:
            results.extend(
                self._prefix_check(
                    name,
                    lintable=file,
                    lineno=task[LINE_NUMBER_KEY],
                ),
            )

        notify = task.get("notify")
        if notify:
            if isinstance(notify, str):
                notify = [notify]
            results.extend(
                [
                    self.create_matcherror(
                        message=f"Task notify '{handler}' should start with an uppercase letter.",
                        lineno=task[LINE_NUMBER_KEY],
                        tag="name[casing]",
                        filename=file,
                    )
                    for handler in notify
                    if handler[0].isalpha()
                    and handler[0].islower()
                    and not handler[0].isupper()
                ],
            )
        return results

    def _prefix_check(
        self,
        name: str,
        lintable: Lintable | None,
        lineno: int,
    ) -> list[MatchError]:
        results: list[MatchError] = []
        effective_name = name
        if lintable is None:
            return []

        if not results:
            results.extend(
                self._check_name(
                    effective_name,
                    lintable=lintable,
                    lineno=lineno,
                ),
            )
        return results

    def _check_name(
        self,
        name: str,
        lintable: Lintable | None,
        lineno: int,
    ) -> list[MatchError]:
        # This rules applies only to languages that do have uppercase and
        # lowercase letter, so we ignore anything else. On Unicode isupper()
        # is not necessarily the opposite of islower()
        results = []
        # stage one check prefix
        effective_name = name
        if self._collection and lintable:
            full_stem = self._find_full_stem(lintable)
            stems = [
                self._collection.options.task_name_prefix.format(stem=stem)
                for stem in wcmatch.pathlib.PurePath(
                    full_stem,
                ).parts
            ]
            prefix = "".join(stems)
            if lintable.kind == "tasks" and full_stem != "main":
                if not name.startswith(prefix):
                    # For the moment in order to raise errors this rule needs to be
                    # enabled manually. Still, we do allow use of prefixes even without
                    # having to enable the rule.
                    if "name[prefix]" in self._collection.options.enable_list:
                        results.append(
                            self.create_matcherror(
                                message=f"Task name should start with '{prefix}'.",
                                lineno=lineno,
                                tag="name[prefix]",
                                filename=lintable,
                            ),
                        )
                        return results
                else:
                    effective_name = name[len(prefix) :]

        if (
            effective_name[0].isalpha()
            and effective_name[0].islower()
            and not effective_name[0].isupper()
        ):
            results.append(
                self.create_matcherror(
                    message="All names should start with an uppercase letter.",
                    lineno=lineno,
                    tag="name[casing]",
                    filename=lintable,
                ),
            )
        if self._re_templated_inside.match(name):
            results.append(
                self.create_matcherror(
                    message="Jinja templates should only be at the end of 'name'",
                    lineno=lineno,
                    tag="name[template]",
                    filename=lintable,
                ),
            )
        return results

    def _find_full_stem(self, lintable: Lintable) -> str:
        lintable_dir = wcmatch.pathlib.PurePath(lintable.dir)
        stem = lintable.path.stem
        kind = str(lintable.kind)

        stems = [lintable_dir.name]
        lintable_dir = lintable_dir.parent
        pathex = lintable_dir / stem
        for entry in self.options.kinds:
            for key, value in entry.items():
                if kind == key:
                    glob = value

        while pathex.globmatch(
            glob,
            flags=(
                wcmatch.pathlib.GLOBSTAR
                | wcmatch.pathlib.BRACE
                | wcmatch.pathlib.DOTGLOB
            ),
        ):
            stems.insert(0, lintable_dir.name)
            lintable_dir = lintable_dir.parent
            pathex = lintable_dir / stem

        if stems[0].startswith(kind):
            del stems[0]
        return str(wcmatch.pathlib.PurePath(*stems, stem))

    def transform(
        self,
        match: MatchError,
        lintable: Lintable,
        data: CommentedMap | CommentedSeq | str,
    ) -> None:
        if match.tag == "name[casing]":

            def update_task_name(task_name: str) -> str:
                """Capitalize the first work of the task name."""
                # Not using capitalize(), since that rewrites the rest of the name to lower case
                if "|" in task_name:  # if using prefix
                    [file_name, update_task_name] = task_name.split("|")
                    return f"{file_name.strip()} | {update_task_name.strip()[:1].upper()}{update_task_name.strip()[1:]}"

                return f"{task_name[:1].upper()}{task_name[1:]}"

            target_task = self.seek(match.yaml_path, data)
            orig_task_name = target_task.get("name", None)
            # pylint: disable=too-many-nested-blocks
            if orig_task_name:
                updated_task_name = update_task_name(orig_task_name)
                for item in data:
                    if isinstance(item, dict) and "tasks" in item:
                        for task in item["tasks"]:
                            # We want to rewrite task names in the notify keyword, but
                            # if there isn't a notify section, there's nothing to do.
                            if "notify" not in task:
                                continue

                            if (
                                isinstance(task["notify"], str)
                                and orig_task_name == task["notify"]
                            ):
                                task["notify"] = updated_task_name
                            elif isinstance(task["notify"], list):
                                for idx in range(len(task["notify"])):
                                    if orig_task_name == task["notify"][idx]:
                                        task["notify"][idx] = updated_task_name

                    if isinstance(item, dict) and "handlers" in item:
                        for task in item["handlers"]:
                            listener_task_name = task.get("listen", None)
                            if (
                                listener_task_name
                                and listener_task_name == orig_task_name
                            ):
                                task["listen"] = updated_task_name

                target_task["name"] = updated_task_name
                match.fixed = True


if "pytest" in sys.modules:
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    def test_file_positive() -> None:
        """Positive test for name[missing]."""
        collection = RulesCollection()
        collection.register(NameRule())
        success = "examples/playbooks/rule-name-missing-pass.yml"
        good_runner = Runner(success, rules=collection)
        assert [] == good_runner.run()

    def test_file_negative() -> None:
        """Negative test for name[missing]."""
        collection = RulesCollection()
        collection.register(NameRule())
        failure = "examples/playbooks/rule-name-missing-fail.yml"
        bad_runner = Runner(failure, rules=collection)
        errs = bad_runner.run()
        assert len(errs) == 5

    def test_name_prefix_positive(config_options: Options) -> None:
        """Positive test for name[prefix]."""
        config_options.enable_list = ["name[prefix]"]
        collection = RulesCollection(options=config_options)
        collection.register(NameRule())
        success = Lintable(
            "examples/playbooks/tasks/main.yml",
            kind="tasks",
        )
        good_runner = Runner(success, rules=collection)
        results = good_runner.run()
        assert len(results) == 0

    def test_name_prefix_negative(config_options: Options) -> None:
        """Negative test for name[missing]."""
        config_options.enable_list = ["name[prefix]"]
        collection = RulesCollection(options=config_options)
        collection.register(NameRule())
        failure = Lintable(
            "examples/playbooks/tasks/rule-name-prefix-fail.yml",
            kind="tasks",
        )
        bad_runner = Runner(failure, rules=collection)
        results = bad_runner.run()
        assert len(results) == 3
        # , "\n".join(results)
        assert results[0].tag == "name[casing]"
        assert results[1].tag == "name[prefix]"
        assert results[2].tag == "name[prefix]"

    def test_name_prefix_negative_2(config_options: Options) -> None:
        """Negative test for name[prefix]."""
        config_options.enable_list = ["name[prefix]"]
        collection = RulesCollection(options=config_options)
        collection.register(NameRule())
        failure = Lintable(
            "examples/playbooks/tasks/partial_prefix/foo.yml",
            kind="tasks",
        )
        bad_runner = Runner(failure, rules=collection)
        results = bad_runner.run()
        assert len(results) == 2
        assert results[0].tag == "name[prefix]"
        assert results[1].tag == "name[prefix]"

    def test_name_prefix_negative_3(config_options: Options) -> None:
        """Negative test for name[prefix]."""
        config_options.enable_list = ["name[prefix]"]
        collection = RulesCollection(options=config_options)
        collection.register(NameRule())
        failure = Lintable(
            "examples/playbooks/tasks/partial_prefix/main.yml",
            kind="tasks",
        )
        bad_runner = Runner(failure, rules=collection)
        results = bad_runner.run()
        assert len(results) == 2
        assert results[0].tag == "name[prefix]"
        assert results[1].tag == "name[prefix]"

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

    def test_rule_notify_lowercase() -> None:
        """Negative test for a task notify that starts with lowercase."""
        collection = RulesCollection()
        collection.register(NameRule())
        failure = "examples/playbooks/name_case_notify_fail.yml"
        bad_runner = Runner(failure, rules=collection)
        errs = bad_runner.run()
        assert len(errs) == 4
        assert errs[0].tag == "name[casing]"
        assert errs[1].tag == "name[casing]"
        assert errs[2].tag == "name[casing]"
        assert errs[3].tag == "name[casing]"
        assert errs[0].rule.id == "name"
        assert errs[1].rule.id == "name"
        assert errs[2].rule.id == "name"
        assert errs[3].rule.id == "name"

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

    def test_when_no_lintable() -> None:
        """Test when lintable is None."""
        name_rule = NameRule()
        result = name_rule._prefix_check("Foo", None, 1)  # noqa: SLF001
        assert len(result) == 0
