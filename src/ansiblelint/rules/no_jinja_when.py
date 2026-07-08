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
RE_QUOTED_STRING = re.compile(r'"[^"]*"|\'[^\']*\'')


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
        if match.tag == self.id:
            task = self.seek(match.yaml_path, data)
            key_to_check = ("when", "changed_when", "failed_when")
            changed = False
            for _ in range(len(task)):
                if isinstance(task, MutableMapping):
                    for k, v in task.items():
                        if k == "roles" and isinstance(v, list):
                            changed = (
                                transform_for_roles(v, key_to_check=key_to_check)
                                or changed
                            )
                        elif k in key_to_check and isinstance(v, str):
                            new_v = _strip_redundant_jinja(v)
                            if new_v != v:
                                task[k] = new_v
                                changed = True
            match.fixed = changed


def _fix_value(value: Any) -> Any:
    """Apply _strip_redundant_jinja to a string or a list of strings."""
    if isinstance(value, list):
        return [
            _strip_redundant_jinja(item) if isinstance(item, str) else item
            for item in value
        ]
    if isinstance(value, str):
        return _strip_redundant_jinja(value)
    return value


def transform_for_roles(v: list[Any], key_to_check: tuple[str, ...]) -> bool:
    """Additional transform logic in case of roles.

    Returns whether any value was actually changed.
    """
    changed = False
    for new_dict in v:
        for new_key, new_value in new_dict.items():
            if new_key not in key_to_check:
                continue
            fixed_value = _fix_value(new_value)
            if fixed_value != new_value:
                new_dict[new_key] = fixed_value
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
