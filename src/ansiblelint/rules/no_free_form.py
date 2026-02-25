"""Implementation of NoFreeFormRule."""

from __future__ import annotations

import functools
import re
import sys
from typing import TYPE_CHECKING, Any

from ansible.errors import AnsibleParserError
from ansible.parsing.splitter import split_args
from ruamel.yaml.scalarstring import DoubleQuotedScalarString, SingleQuotedScalarString

from ansiblelint.constants import INCLUSION_ACTION_NAMES
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
    version_changed = "6.8.0"
    needs_raw_task = True
    cmd_shell_re = re.compile(
        r"(chdir|creates|executable|removes|stdin|stdin_add_newline|warn)=",
    )
    _ids = {
        "no-free-form[raw]": "Avoid embedding `executable=` inside raw calls, use explicit args dictionary instead.",
        "no-free-form[raw-non-string]": "Passing a non string value to `raw` module is neither documented or supported.",
    }

    @staticmethod
    def _has_unmatched_quote(val: str) -> bool:
        """Detect values starting with a quote but lacking a closing match."""
        if not val:
            return False
        if val[0] in "\"'":
            if len(val) == 1:
                return True
            return val[-1] != val[0]
        return False

    @staticmethod
    def _normalize_value(val: str) -> Any:
        """Normalize quoted values while keeping Jinja/spacing intact."""
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            return (
                DoubleQuotedScalarString if val[0] == '"' else SingleQuotedScalarString
            )(val[1:-1])
        return val

    @classmethod
    def _parse_module_opts(cls, value: str) -> dict[str, Any]:
        """Parse module opts, falling back to cmd on unbalanced quotes."""
        try:
            parts = split_args(value)  # type: ignore[no-untyped-call]
        except AnsibleParserError:
            return {"cmd": value}
        module_opts: dict[str, Any] = {}
        cmd_parts: list[str] = []
        for part in parts:
            if "=" in part:
                key, raw_value = part.split("=", 1)
                if cls._has_unmatched_quote(raw_value):
                    return {"cmd": value}
                module_opts[key] = cls._normalize_value(raw_value)
            else:
                cmd_parts.append(part)
        if cmd_parts:
            module_opts["cmd"] = " ".join(cmd_parts)
        return module_opts

    @classmethod
    def _parse_raw_value(cls, value: str) -> tuple[str, dict[str, Any]]:
        """Parse raw module string, extracting executable when possible."""
        try:
            parts = split_args(value)  # type: ignore[no-untyped-call]
        except AnsibleParserError:
            return value, {}
        exec_key_val: dict[str, Any] = {}
        raw_cmd_parts: list[str] = []
        for part in parts:
            if part.startswith("executable="):
                _, raw_value = part.split("=", 1)
                exec_key_val["executable"] = cls._normalize_value(raw_value)
            else:
                raw_cmd_parts.append(part)
        return " ".join(raw_cmd_parts), exec_key_val

    @staticmethod
    def _sorted_module_opts(module_opts: dict[str, Any]) -> dict[str, Any]:
        sorted_module_opts: dict[str, Any] = {}
        for key in sorted(
            module_opts.keys(),
            key=functools.cmp_to_key(task_property_sorter),
        ):
            sorted_module_opts[key] = module_opts[key]
        return sorted_module_opts

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
                            lineno=task.line,
                            filename=file,
                            tag=f"{self.id}[raw]",
                        ),
                    )
            else:
                results.append(
                    self.create_matcherror(
                        message="Passing a non string value to `raw` module is neither documented or supported.",
                        lineno=task.line,
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
                if self.cmd_shell_re.search(action_value):
                    fail = True
            else:
                fail = True
            if fail:
                results.append(
                    self.create_matcherror(
                        message=f"Avoid using free-form when calling module actions. ({action})",
                        lineno=task.line,
                        filename=file,
                        details=action,
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

            if match.tag == "no-free-form":
                target_module = match.details

                for _ in range(len(task)):
                    k, v = task.popitem(False)
                    # identify module as key and process its value
                    if k == target_module and isinstance(v, str):
                        module_opts = self._parse_module_opts(v)
                        task[k] = self._sorted_module_opts(module_opts)
                    else:
                        task[k] = v

                match.fixed = True
            elif match.tag == "no-free-form[raw]":
                for _ in range(len(task)):
                    k, v = task.popitem(False)
                    if isinstance(v, str) and "executable" in v:
                        raw_value, exec_key_val = self._parse_raw_value(v)
                        task[k] = raw_value
                        if exec_key_val:
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
            pytest.param("examples/playbooks/rule-no-free-form-fail.yml", 6, id="fail"),
        ),
    )
    def test_rule_no_free_form(
        default_rules_collection: RulesCollection,
        file: str,
        expected: int,
    ) -> None:
        """Validate that rule works as intended."""
        results = Runner(file, rules=default_rules_collection).run()

        rule_results = [r for r in results if r.rule.id == NoFreeFormRule.id]

        for result in rule_results:
            assert result.rule.id == NoFreeFormRule.id, result
        assert len(rule_results) == expected

    def test_no_free_form_transform_error_handling() -> None:
        """Test that transform handles malformed quoted strings."""
        from ruamel.yaml.comments import CommentedMap

        from ansiblelint.errors import MatchError

        rule = NoFreeFormRule()
        task = CommentedMap({"ansible.builtin.shell": 'chdir=" /tmp echo foo'})
        match = MatchError(
            message="test",
            rule=rule,
            details="ansible.builtin.shell",
            tag="no-free-form",
        )

        rule.transform(match, None, task)  # type: ignore[arg-type]
        assert task["ansible.builtin.shell"] == {"cmd": 'chdir=" /tmp echo foo'}

    def test_no_free_form_transform_jinja_with_spaces() -> None:
        """Test that Jinja expressions with spaces are preserved."""
        from ruamel.yaml.comments import CommentedMap

        from ansiblelint.errors import MatchError

        rule = NoFreeFormRule()
        task = CommentedMap(
            {"ansible.builtin.dnf": "name={{ item }} state=latest"},
        )
        match = MatchError(
            message="test",
            rule=rule,
            details="ansible.builtin.dnf",
            tag="no-free-form",
        )

        rule.transform(match, None, task)  # type: ignore[arg-type]
        assert task["ansible.builtin.dnf"]["name"] == "{{ item }}"
        assert task["ansible.builtin.dnf"]["state"] == "latest"
        assert "cmd" not in task["ansible.builtin.dnf"]

    def test_no_free_form_transform_unmatched_quote_value() -> None:
        """Test that malformed quoted values fall back to cmd."""
        from ruamel.yaml.comments import CommentedMap

        from ansiblelint.errors import MatchError

        rule = NoFreeFormRule()
        task = CommentedMap(
            {"ansible.builtin.command": 'name="foo"bar chdir=/tmp'},
        )
        match = MatchError(
            message="test",
            rule=rule,
            details="ansible.builtin.command",
            tag="no-free-form",
        )

        rule.transform(match, None, task)  # type: ignore[arg-type]
        assert task["ansible.builtin.command"] == {
            "cmd": 'name="foo"bar chdir=/tmp',
        }

    def test_no_free_form_transform_raw_unbalanced_executable() -> None:
        """Test raw transform fallback when executable value is unbalanced."""
        from ruamel.yaml.comments import CommentedMap

        from ansiblelint.errors import MatchError

        rule = NoFreeFormRule()
        task = CommentedMap(
            {"ansible.builtin.raw": 'executable="/bin/bash echo foo'},
        )
        match = MatchError(
            message="test",
            rule=rule,
            tag="no-free-form[raw]",
        )

        rule.transform(match, None, task)  # type: ignore[arg-type]
        assert task["ansible.builtin.raw"] == 'executable="/bin/bash echo foo'
        assert "args" not in task
