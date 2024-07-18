"""Tests for args rule."""

from ansiblelint.file_utils import Lintable
from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner


def test_args_module_relative_import(default_rules_collection: RulesCollection) -> None:
    """Validate args check of a module with a relative import."""
    lintable = Lintable(
        "examples/playbooks/module_relative_import.yml",
        kind="playbook",
    )
    result = Runner(lintable, rules=default_rules_collection).run()
    assert len(result) == 1, result
    assert result[0].lineno == 5
    assert result[0].filename == "examples/playbooks/module_relative_import.yml"
    assert result[0].tag == "args[module]"
    assert result[0].message == "missing required arguments: name"
