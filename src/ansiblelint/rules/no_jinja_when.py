"""Implementation of no-jinja-when rule."""

from __future__ import annotations

import re
import sys
from collections.abc import MutableMapping
from typing import TYPE_CHECKING, Any

from ansiblelint.rules import AnsibleLintRule, TransformMixin

if TYPE_CHECKING:
    from ruamel.yaml.comments import CommentedMap, CommentedSeq

    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task

RE_JINJA = re.compile(r"{{ (.*?) }}")
RE_QUOTED_STRING = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')
_WHEN_KEYS = ("when", "changed_when", "failed_when")


def _strip_redundant_jinja(value: str) -> str:
    for quoted in RE_QUOTED_STRING.findall(value):
        inner = quoted[1:-1]
        if "{{" in inner:
            # {{ }} embedded in a quoted string changes meaning if stripped; skip it
            return value
    return RE_JINJA.sub(r"\1", value)


class NoFormattingInWhenRule(AnsibleLintRule, TransformMixin):
    """No Jinja2 in when."""

    id = "no-jinja-when"
    description = (
        "``when`` is a raw Jinja2 expression, remove redundant {{ }} from variable(s)."
    )
    severity = "HIGH"
    tags = ["deprecations"]
    version_changed = "6.20.0"

    @staticmethod
    def _is_valid(when: str) -> bool:
        if isinstance(when, list):
            for item in when:
                if (
                    isinstance(item, str)
                    and item.find("{{") != -1
                    and item.find("}}") != -1
                ):
                    return False
            return True
        if not isinstance(when, str):
            return True
        return when.find("{{") == -1 and when.find("}}") == -1

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        errors: list[MatchError] = []
        if isinstance(data, dict):
            if "roles" not in data or data["roles"] is None:
                return errors
            errors = [
                self.create_matcherror(
                    details=str({"when": role}),
                    filename=file,
                    data=role,
                )
                for role in data["roles"]
                if (
                    isinstance(role, dict)
                    and "when" in role
                    and not self._is_valid(role["when"])
                )
            ]
        return errors

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> bool | str:
        return "when" in task.raw_task and not self._is_valid(task.raw_task["when"])

    def transform(
        self,
        match: MatchError,
        lintable: Lintable,
        data: CommentedMap | CommentedSeq | str,
    ) -> None:
        if match.tag != self.id:
            return
        task = self.seek(match.yaml_path, data)
        if isinstance(task, MutableMapping):
            match.fixed = _transform_when_keys(task, _WHEN_KEYS)


def _transform_when_value(value: Any) -> tuple[Any, bool]:
    """Return the transformed value and whether it changed.

    Lists are edited in place so that ruamel keeps their comments and blank lines.
    """
    if isinstance(value, list):
        changed = False
        for index, item in enumerate(value):
            if isinstance(item, str):
                new_item = _strip_redundant_jinja(item)
                if new_item != item:
                    value[index] = new_item
                    changed = True
        return value, changed
    if isinstance(value, str):
        new_value = _strip_redundant_jinja(value)
        return new_value, new_value != value
    return value, False


def _transform_when_keys(
    task: MutableMapping[str, Any],
    key_to_check: tuple[str, ...],
) -> bool:
    """Return whether any value was actually changed."""
    changed = False
    for key, value in task.items():
        if key == "roles" and isinstance(value, list):
            changed = transform_for_roles(value, key_to_check=key_to_check) or changed
        elif key in key_to_check:
            new_value, value_changed = _transform_when_value(value)
            if value_changed:
                task[key] = new_value
                changed = True
    return changed


def transform_for_roles(v: list[Any], key_to_check: tuple[str, ...]) -> bool:
    """Additional transform logic in case of roles.

    Returns whether any value was actually changed.
    """
    changed = False
    for role in v:
        if not isinstance(role, MutableMapping):
            continue
        for key, value in role.items():
            if key in key_to_check:
                new_value, value_changed = _transform_when_value(value)
                if value_changed:
                    role[key] = new_value
                    changed = True
    return changed


if "pytest" in sys.modules:
    # Tests for no-jinja-when rule.
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    def test_jinja_file_positive(empty_rule_collection: RulesCollection) -> None:
        """Positive test for no-jinja-when."""
        empty_rule_collection.register(NoFormattingInWhenRule())
        success = "examples/playbooks/rule-no-jinja-when-pass.yml"
        good_runner = Runner(success, rules=empty_rule_collection)
        assert good_runner.run() == []

    def test_jinja_file_negative(empty_rule_collection: RulesCollection) -> None:
        """Negative test for no-jinja-when."""
        empty_rule_collection.register(NoFormattingInWhenRule())
        failure = "examples/playbooks/rule-no-jinja-when-fail.yml"
        bad_runner = Runner(failure, rules=empty_rule_collection)
        errs = bad_runner.run()
        assert len(errs) == 3

    def test_transform_when_value_preserves_non_strings() -> None:
        """Autofix must leave non-string when list items untouched."""
        assert _transform_when_value([True, "{{ foo }}", 1]) == ([True, "foo", 1], True)
        assert _transform_when_value(True) == (True, False)

    def test_transform_for_roles_skips_shorthand_strings() -> None:
        """Shorthand role strings must not break transform iteration."""
        roles: list[Any] = [
            "geerlingguy.nginx",
            {"role": "demo", "when": "{{ bar }}"},
        ]
        transform_for_roles(roles, key_to_check=_WHEN_KEYS)
        assert roles[0] == "geerlingguy.nginx"
        assert roles[1]["when"] == "bar"

    def test_strip_redundant_jinja_skips_quoted_templates() -> None:
        """Autofix must skip templates embedded in a quoted string."""
        assert _strip_redundant_jinja("{{ foo }}") == "foo"
        assert _strip_redundant_jinja("'{{ v }}' == '8'") == "'{{ v }}' == '8'"
        assert (
            _strip_redundant_jinja('not "version={{ v }}" in stdout')
            == 'not "version={{ v }}" in stdout'
        )

    def test_strip_redundant_jinja_handles_escaped_quotes() -> None:
        """An escaped quote must not be mistaken for the closing delimiter."""
        escaped = r"'it\'s {{ v }}' == x"
        assert _strip_redundant_jinja(escaped) == escaped
        assert _strip_redundant_jinja('{{ ansible_facts["os_family"] }}') == (
            'ansible_facts["os_family"]'
        )
