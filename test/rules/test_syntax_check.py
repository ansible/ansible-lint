"""Tests for syntax-check rule."""
from typing import Any

from ansiblelint.file_utils import Lintable
from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner


def test_get_ansible_syntax_check_matches(
    default_rules_collection: RulesCollection,
) -> None:
    """Validate parsing of ansible output."""
    lintable = Lintable(
        "examples/playbooks/conflicting_action.yml",
        kind="playbook",
    )

    result = Runner(lintable, rules=default_rules_collection).run()

    assert result[0].lineno == 4
    assert result[0].column == 7
    assert (
        result[0].message
        == "conflicting action statements: ansible.builtin.debug, ansible.builtin.command"
    )
    # We internally convert absolute paths returned by ansible into paths
    # relative to current directory.
    assert result[0].filename.endswith("/conflicting_action.yml")
    assert len(result) == 1


def test_empty_playbook(default_rules_collection: RulesCollection) -> None:
    """Validate detection of empty-playbook."""
    lintable = Lintable("examples/playbooks/empty_playbook.yml", kind="playbook")
    result = Runner(lintable, rules=default_rules_collection).run()
    assert result[0].lineno == 1
    # We internally convert absolute paths returned by ansible into paths
    # relative to current directory.
    assert result[0].filename.endswith("/empty_playbook.yml")
    assert result[0].tag == "syntax-check[empty-playbook]"
    assert result[0].message == "Empty playbook, nothing to do"
    assert len(result) == 1


def test_extra_vars_passed_to_command(
    default_rules_collection: RulesCollection,
    config_options: Any,
) -> None:
    """Validate `extra-vars` are passed to syntax check command."""
    config_options.extra_vars = {
        "foo": "bar",
        "complex_variable": ":{;\t$()",
    }
    lintable = Lintable("examples/playbooks/extra_vars.yml", kind="playbook")

    result = Runner(lintable, rules=default_rules_collection).run()

    assert not result


def test_syntax_check_role() -> None:
    """Validate syntax check of a broken role."""
    lintable = Lintable("examples/playbooks/roles/invalid_due_syntax", kind="role")
    rules = RulesCollection()
    result = Runner(lintable, rules=rules).run()
    assert len(result) == 1, result
    assert result[0].lineno == 2
    assert result[0].filename == "examples/roles/invalid_due_syntax/tasks/main.yml"
    assert result[0].tag == "syntax-check[specific]"
    assert result[0].message == "no module/action detected in task."
