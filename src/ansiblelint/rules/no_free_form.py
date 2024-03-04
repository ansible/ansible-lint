"""Implementation of NoFreeFormRule."""

from __future__ import annotations

import functools
import re
import sys
from typing import TYPE_CHECKING, Any

from ansiblelint.constants import INCLUSION_ACTION_NAMES, LINE_NUMBER_KEY
from ansiblelint.rules import AnsibleLintRule, TransformMixin
from ansiblelint.rules.key_order import task_property_sorter

if TYPE_CHECKING:
    from ruamel.yaml.comments import CommentedMap, CommentedSeq

    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task


class NoFreeFormRule(AnsibleLintRule, TransformMixin):
    """Rule for detecting discouraged free-form syntax for action modules."""

    id = "no-free-form"
    description = "Avoid free-form inside files as it can produce subtle bugs."
    severity = "MEDIUM"
    tags = ["syntax", "risk"]
    version_added = "v6.8.0"
    needs_raw_task = True
    cmd_shell_re = re.compile(
        r"(chdir|creates|executable|removes|stdin|stdin_add_newline|warn)=",
    )
    _ids = {
        "no-free-form[raw]": "Avoid embedding `executable=` inside raw calls, use explicit args dictionary instead.",
        "no-free-form[raw-non-string]": "Passing a non string value to `raw` module is neither documented or supported.",
    }

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> list[MatchError]:
        results: list[MatchError] = []
        action = task["action"]["__ansible_module_original__"]

        if action in INCLUSION_ACTION_NAMES:
            return results

        action_value = task["__raw_task__"].get(action, None)
        if task["action"].get("__ansible_module__", None) == "raw":
            if isinstance(action_value, str):
                if "executable=" in action_value:
                    results.append(
                        self.create_matcherror(
                            message="Avoid embedding `executable=` inside raw calls, use explicit args dictionary instead.",
                            lineno=task[LINE_NUMBER_KEY],
                            filename=file,
                            tag=f"{self.id}[raw]",
                        ),
                    )
            else:
                results.append(
                    self.create_matcherror(
                        message="Passing a non string value to `raw` module is neither documented or supported.",
                        lineno=task[LINE_NUMBER_KEY],
                        filename=file,
                        tag=f"{self.id}[raw-non-string]",
                    ),
                )
        elif isinstance(action_value, str) and "=" in action_value:
            fail = False
            if task["action"].get("__ansible_module__") in (
                "ansible.builtin.command",
                "ansible.builtin.shell",
                "ansible.windows.win_command",
                "ansible.windows.win_shell",
                "command",
                "shell",
                "win_command",
                "win_shell",
            ):
                if self.cmd_shell_re.match(action_value):
                    fail = True
            else:
                fail = True
            if fail:
                results.append(
                    self.create_matcherror(
                        message=f"Avoid using free-form when calling module actions. ({action})",
                        lineno=task[LINE_NUMBER_KEY],
                        filename=file,
                    ),
                )
        return results

    def transform(
        self,
        match: MatchError,
        lintable: Lintable,
        data: CommentedMap | CommentedSeq | str,
    ) -> None:
        if "no-free-form" in match.tag:
            task = self.seek(match.yaml_path, data)

            def filter_values(
                val: str,
                filter_key: str,
                filter_dict: dict[str, Any],
            ) -> bool:
                """Return True if module option is not present in the string."""
                if filter_key not in val:
                    return True

                [k, v] = val.split(filter_key)
                filter_dict[k] = v
                return False

            if match.tag == "no-free-form":
                module_opts: dict[str, Any] = {}
                for _ in range(len(task)):
                    k, v = task.popitem(False)
                    # identify module as key and process its value
                    if len(k.split(".")) == 3 and isinstance(v, str):
                        # if it is a message
                        if "msg" in v:
                            filter_values(v, "=", module_opts)
                        else:
                            # Filter the module options and command
                            module_opts["cmd"] = " ".join(
                                [
                                    item
                                    for item in v.split(" ")
                                    if filter_values(item, "=", module_opts)
                                ],
                            )

                        sorted_module_opts = {}
                        for key in sorted(
                            module_opts.keys(),
                            key=functools.cmp_to_key(task_property_sorter),
                        ):
                            sorted_module_opts[key] = module_opts[key]

                        task[k] = sorted_module_opts
                    else:
                        task[k] = v

                match.fixed = True
            elif match.tag == "no-free-form[raw]":
                exec_key_val: dict[str, Any] = {}
                for _ in range(len(task)):
                    k, v = task.popitem(False)
                    if isinstance(v, str) and "executable" in v:
                        # Filter the executable and other parts from the string
                        task[k] = " ".join(
                            [
                                item
                                for item in v.split(" ")
                                if filter_values(item, "=", exec_key_val)
                            ],
                        )
                        task["args"] = exec_key_val
                    else:
                        task[k] = v
                match.fixed = True


if "pytest" in sys.modules:
    import pytest

    # pylint: disable=ungrouped-imports
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    @pytest.mark.parametrize(
        ("file", "expected"),
        (
            pytest.param("examples/playbooks/rule-no-free-form-pass.yml", 0, id="pass"),
            pytest.param("examples/playbooks/rule-no-free-form-fail.yml", 3, id="fail"),
        ),
    )
    def test_rule_no_free_form(
        default_rules_collection: RulesCollection,
        file: str,
        expected: int,
    ) -> None:
        """Validate that rule works as intended."""
        results = Runner(file, rules=default_rules_collection).run()

        for result in results:
            assert result.rule.id == NoFreeFormRule.id, result
        assert len(results) == expected
