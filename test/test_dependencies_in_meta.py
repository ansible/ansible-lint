"""Tests about dependencies in meta."""
from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner


def test_external_dependency_is_ok(default_rules_collection: RulesCollection) -> None:
    """Check that external dep in role meta is not a violation."""
    playbook_path = "examples/roles/dependency_in_meta/meta/main.yml"
    good_runner = Runner(playbook_path, rules=default_rules_collection)
    assert [] == good_runner.run()
