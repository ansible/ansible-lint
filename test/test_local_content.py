"""Test playbooks with local content."""
from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner


def test_local_collection(default_rules_collection: RulesCollection) -> None:
    """Assures local collections are found."""
    playbook_path = "test/local-content/test-collection.yml"
    runner = Runner(playbook_path, rules=default_rules_collection)
    results = runner.run()

    assert len(runner.lintables) == 1
    assert len(results) == 0
