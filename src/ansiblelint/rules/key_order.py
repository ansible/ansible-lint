"""All tasks should be have name come first."""

from __future__ import annotations

import functools
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ansiblelint.constants import ANNOTATION_KEYS, LINE_NUMBER_KEY
from ansiblelint.errors import MatchError, RuleMatchTransformMeta
from ansiblelint.rules import AnsibleLintRule, TransformMixin

if TYPE_CHECKING:
    from ruamel.yaml.comments import CommentedMap, CommentedSeq

    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task


SORTER_TASKS = (
    "name",
    # "__module__",
    # "action",
    # "args",
    None,  # <-- None include all modules that not using action and *
    # "when",
    # "notify",
    # "tags",
    "block",
    "rescue",
    "always",
)


def get_property_sort_index(name: str) -> int:
    """Return the index of the property in the sorter."""
    a_index = -1
    for i, v in enumerate(SORTER_TASKS):
        if v == name:
            return i
        if v is None:
            a_index = i
    return a_index


def task_property_sorter(property1: str, property2: str) -> int:
    """Sort task properties based on SORTER."""
    v_1 = get_property_sort_index(property1)
    v_2 = get_property_sort_index(property2)
    return (v_1 > v_2) - (v_1 < v_2)


@dataclass(frozen=True)
class KeyOrderTMeta(RuleMatchTransformMeta):
    """Key Order transform metadata.

    :param fixed: tuple with updated key order
    """

    fixed: tuple[str | int, ...]

    def __str__(self) -> str:
        """Return string representation."""
        return f"Fixed to {self.fixed}"


class KeyOrderRule(AnsibleLintRule, TransformMixin):
    """Ensure specific order of keys in mappings."""

    id = "key-order"
    shortdesc = __doc__
    severity = "LOW"
    tags = ["formatting"]
    version_added = "v6.6.2"
    needs_raw_task = True
    _ids = {
        "key-order[task]": "You can improve the task key order",
    }

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        """Return matches found for a specific play (entry in playbook)."""
        result: list[MatchError] = []
        if file.kind != "playbook":
            return result
        keys = [str(key) for key, val in data.items() if key not in ANNOTATION_KEYS]
        sorted_keys = sorted(keys, key=functools.cmp_to_key(task_property_sorter))
        if keys != sorted_keys:
            result.append(
                self.create_matcherror(
                    f"You can improve the play key order to: {', '.join(sorted_keys)}",
                    filename=file,
                    tag=f"{self.id}[play]",
                    lineno=data[LINE_NUMBER_KEY],
                    transform_meta=KeyOrderTMeta(fixed=tuple(sorted_keys)),
                ),
            )
        return result

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> list[MatchError]:
        result = []
        raw_task = task["__raw_task__"]
        keys = [str(key) for key in raw_task if not key.startswith("_")]
        sorted_keys = sorted(keys, key=functools.cmp_to_key(task_property_sorter))
        if keys != sorted_keys:
            result.append(
                self.create_matcherror(
                    f"You can improve the task key order to: {', '.join(sorted_keys)}",
                    filename=file,
                    tag="key-order[task]",
                    transform_meta=KeyOrderTMeta(fixed=tuple(sorted_keys)),
                ),
            )
        return result

    def transform(
        self,
        match: MatchError,
        lintable: Lintable,
        data: CommentedMap | CommentedSeq | str,
    ) -> None:
        if not isinstance(match.transform_meta, KeyOrderTMeta):
            return

        if match.tag == f"{self.id}[play]":
            play = self.seek(match.yaml_path, data)
            for key in match.transform_meta.fixed:
                # other transformation might change the key
                if key in play:
                    play[key] = play.pop(key)
            match.fixed = True
        if match.tag == f"{self.id}[task]":
            task = self.seek(match.yaml_path, data)
            for key in match.transform_meta.fixed:
                # other transformation might change the key
                if key in task:
                    task[key] = task.pop(key)
            match.fixed = True


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    import pytest

    # pylint: disable=ungrouped-imports
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    @pytest.mark.parametrize(
        ("test_file", "failures"),
        (
            pytest.param("examples/playbooks/rule-key-order-pass.yml", 0, id="pass"),
            pytest.param("examples/playbooks/rule-key-order-fail.yml", 6, id="fail"),
        ),
    )
    def test_key_order_rule(
        default_rules_collection: RulesCollection,
        test_file: str,
        failures: int,
    ) -> None:
        """Test rule matches."""
        results = Runner(test_file, rules=default_rules_collection).run()
        assert len(results) == failures
        for result in results:
            assert result.rule.id == "key-order"

    @pytest.mark.parametrize(
        ("properties", "expected"),
        (
            pytest.param([], []),
            pytest.param(["block", "name"], ["name", "block"]),
            pytest.param(
                ["block", "name", "action", "..."],
                ["name", "action", "...", "block"],
            ),
        ),
    )
    def test_key_order_property_sorter(
        properties: list[str],
        expected: list[str],
    ) -> None:
        """Test the task property sorter."""
        result = sorted(properties, key=functools.cmp_to_key(task_property_sorter))
        assert expected == result

    @pytest.mark.parametrize(
        ("key", "order"),
        (
            pytest.param("name", 0),
            pytest.param("action", 1),
            pytest.param("foobar", SORTER_TASKS.index(None)),
            pytest.param("block", len(SORTER_TASKS) - 3),
            pytest.param("rescue", len(SORTER_TASKS) - 2),
            pytest.param("always", len(SORTER_TASKS) - 1),
        ),
    )
    def test_key_order_property_sort_index(key: str, order: int) -> None:
        """Test sorting index."""
        assert get_property_sort_index(key) == order

    @pytest.mark.parametrize(
        ("prop1", "prop2", "result"),
        (
            pytest.param("name", "block", -1),
            pytest.param("block", "name", 1),
            pytest.param("block", "block", 0),
        ),
    )
    def test_key_order_property_sortfunc(prop1: str, prop2: str, result: int) -> None:
        """Test sorting function."""
        assert task_property_sorter(prop1, prop2) == result
