"""All tasks should be have name come first."""
from __future__ import annotations

import functools
import sys
from typing import TYPE_CHECKING

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
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


class KeyOrderRule(AnsibleLintRule):
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

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> list[MatchError]:
        result = []
        raw_task = task["__raw_task__"]
        keys = [key for key in raw_task if not key.startswith("_")]
        sorted_keys = sorted(keys, key=functools.cmp_to_key(task_property_sorter))
        if keys != sorted_keys:
            result.append(
                self.create_matcherror(
                    f"You can improve the task key order to: {', '.join(sorted_keys)}",
                    filename=file,
                    tag="key-order[task]",
                ),
            )
        return result


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    import pytest

    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.runner import Runner  # pylint: disable=ungrouped-imports

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
