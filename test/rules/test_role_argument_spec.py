"""Tests for role-argument-spec rule."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from ansiblelint.config import Options
from ansiblelint.rules import RulesCollection
from ansiblelint.rules.role_argument_spec import RoleArgumentSpec
from ansiblelint.runner import Runner

if TYPE_CHECKING:
    from pathlib import Path

    from ansiblelint.app import App


@pytest.fixture(name="test_rules_collection")
def fixture_test_rules_collection(app: App) -> RulesCollection:
    """Return a rules collection with the RoleArgumentSpec rule enabled."""
    config_options = Options()
    config_options.enable_list = ["role-argument-spec"]
    collection = RulesCollection(app=app, options=config_options)
    collection.register(RoleArgumentSpec())
    return collection


@pytest.mark.parametrize(
    ("role_path", "expected_count"),
    (
        pytest.param(
            "examples/roles/role_argument_spec_missing",
            1,
            id="missing_argument_spec",
        ),
        pytest.param(
            "examples/roles/hello",
            0,
            id="standalone_argument_spec",
        ),
        pytest.param(
            "examples/roles/role_argument_spec_embedded",
            0,
            id="embedded_argument_spec",
        ),
    ),
)
def test_role_argument_spec(
    test_rules_collection: RulesCollection,
    role_path: str,
    expected_count: int,
) -> None:
    """Lint a role and check for role-argument-spec violations."""
    results = Runner(role_path, rules=test_rules_collection).run()
    matched = [r for r in results if r.rule.id == "role-argument-spec"]
    assert len(matched) == expected_count


def dict_to_files(parent_dir: Path, file_dict: dict[str, Any]) -> None:
    """Write a nested dict to a file and directory structure below parent_dir."""
    for name, content in file_dict.items():
        if isinstance(content, dict):
            directory = parent_dir / name
            directory.mkdir(parents=True, exist_ok=True)
            dict_to_files(directory, content)
        else:
            (parent_dir / name).write_text(content)


def test_role_argument_spec_tmpdir_no_spec(
    test_rules_collection: RulesCollection,
    tmp_path: Path,
) -> None:
    """Dynamic role without argument_specs should trigger the rule."""
    role_layout = {
        "tasks": {
            "main.yml": "---\n- name: Test\n  ansible.builtin.debug:\n    msg: hi\n"
        },
        "meta": {"main.yml": "---\ndependencies: []\n"},
    }
    dict_to_files(tmp_path, role_layout)
    results = Runner(str(tmp_path), rules=test_rules_collection).run()
    matched = [r for r in results if r.rule.id == "role-argument-spec"]
    assert len(matched) == 1


def test_role_argument_spec_tmpdir_with_spec(
    test_rules_collection: RulesCollection,
    tmp_path: Path,
) -> None:
    """Dynamic role with argument_specs.yml should pass."""
    role_layout = {
        "tasks": {
            "main.yml": "---\n- name: Test\n  ansible.builtin.debug:\n    msg: hi\n"
        },
        "meta": {
            "main.yml": "---\ndependencies: []\n",
            "argument_specs.yml": (
                "---\nargument_specs:\n  main:\n"
                "    short_description: Test\n"
                "    options:\n"
                "      my_var:\n"
                "        type: str\n"
            ),
        },
    }
    dict_to_files(tmp_path, role_layout)
    results = Runner(str(tmp_path), rules=test_rules_collection).run()
    matched = [r for r in results if r.rule.id == "role-argument-spec"]
    assert len(matched) == 0
