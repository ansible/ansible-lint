"""Test the RoleNames rule."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.role_name import RoleNames
from ansiblelint.runner import Runner

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.fixtures import SubRequest

ROLE_NAME_VALID = "test_role"

TASK_MINIMAL = """
- name: Some task
  ping:
"""

ROLE_MINIMAL = {"tasks": {"main.yml": TASK_MINIMAL}}
ROLE_META_EMPTY = {"meta": {"main.yml": ""}}

ROLE_WITH_EMPTY_META = {**ROLE_MINIMAL, **ROLE_META_EMPTY}

PLAY_INCLUDE_ROLE = f"""
- hosts: all
  roles:
    - {ROLE_NAME_VALID}
"""


@pytest.fixture(name="test_rules_collection")
def fixture_test_rules_collection() -> RulesCollection:
    """Instantiate a roles collection for tests."""
    collection = RulesCollection()
    collection.register(RoleNames())
    return collection


def dict_to_files(parent_dir: Path, file_dict: dict[str, Any]) -> None:
    """Write a nested dict to a file and directory structure below parent_dir."""
    for file, content in file_dict.items():
        if isinstance(content, dict):
            directory = parent_dir / file
            directory.mkdir()
            dict_to_files(directory, content)
        else:
            (parent_dir / file).write_text(content)


@pytest.fixture(name="playbook_path")
def fixture_playbook_path(request: SubRequest, tmp_path: Path) -> str:
    """Create a playbook with a role in a temporary directory."""
    playbook_text = request.param[0]
    role_name = request.param[1]
    role_layout = request.param[2]
    role_path = tmp_path / role_name
    role_path.mkdir()
    dict_to_files(role_path, role_layout)
    play_path = tmp_path / "playbook.yml"
    play_path.write_text(playbook_text)
    return str(play_path)


@pytest.mark.parametrize(
    ("playbook_path", "messages"),
    (
        pytest.param(
            (PLAY_INCLUDE_ROLE, ROLE_NAME_VALID, ROLE_WITH_EMPTY_META),
            [],
            id="ROLE_EMPTY_META",
        ),
    ),
    indirect=("playbook_path",),
)
def test_role_name(
    test_rules_collection: RulesCollection,
    playbook_path: str,
    messages: list[str],
) -> None:
    """Lint a playbook and compare the expected messages with the actual messages."""
    runner = Runner(playbook_path, rules=test_rules_collection)
    results = runner.run()
    assert len(results) == len(messages)
    results_text = str(results)
    for message in messages:
        assert message in results_text
