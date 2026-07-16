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
_WHEN_KEYS = ("when", "changed_when", "failed_when")


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
            _transform_when_keys(task, _WHEN_KEYS)
        match.fixed = True


def _transform_when_value(value: Any) -> Any:
    if isinstance(value, list):
        return [
            RE_JINJA.sub(r"\1", item) if isinstance(item, str) else item
            for item in value
        ]
    if isinstance(value, str):
        return RE_JINJA.sub(r"\1", value)
    return value


def _transform_when_keys(
    task: MutableMapping[str, Any],
    key_to_check: tuple[str, ...],
) -> None:
    for key, value in task.items():
        if key == "roles" and isinstance(value, list):
            transform_for_roles(value, key_to_check=key_to_check)
        elif key in key_to_check:
            task[key] = _transform_when_value(value)


def transform_for_roles(v: list[Any], key_to_check: tuple[str, ...]) -> None:
    """Additional transform logic in case of roles."""
    for role in v:
        if not isinstance(role, MutableMapping):
            continue
        for key, value in role.items():
            if key in key_to_check:
                role[key] = _transform_when_value(value)


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
