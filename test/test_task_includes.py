"""Tests related to task inclusions."""
import pytest

from ansiblelint.file_utils import Lintable
from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner


@pytest.mark.parametrize(
    ("filename", "file_count", "match_count"),
    (
        pytest.param("examples/playbooks/blockincludes.yml", 4, 3, id="blockincludes"),
        pytest.param(
            "examples/playbooks/blockincludes2.yml",
            4,
            3,
            id="blockincludes2",
        ),
        pytest.param("examples/playbooks/taskincludes.yml", 3, 6, id="taskincludes"),
        pytest.param("examples/playbooks/taskimports.yml", 5, 3, id="taskimports"),
        pytest.param(
            "examples/playbooks/include-in-block.yml",
            3,
            1,
            id="include-in-block",
        ),
        pytest.param(
            "examples/playbooks/include-import-tasks-in-role.yml",
            4,
            2,
            id="role_with_task_inclusions",
        ),
    ),
)
def test_included_tasks(
    default_rules_collection: RulesCollection,
    filename: str,
    file_count: int,
    match_count: int,
) -> None:
    """Check if number of loaded files is correct."""
    lintable = Lintable(filename)
    default_rules_collection.options.enable_list = ["name[prefix]"]
    runner = Runner(lintable, rules=default_rules_collection)
    result = runner.run()
    assert len(runner.lintables) == file_count
    assert len(result) == match_count
