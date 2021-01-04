"""Test playbooks with local content."""
from ansiblelint.runner import Runner


def test_local_collection(default_rules_collection):
    """Assures local collections are found."""
    playbook_path = 'test/local-content/test-collection.yml'
    runner = Runner(default_rules_collection, playbook_path, [], [], [])
    results = runner.run()

    assert len(runner.playbooks) == 1
    assert len(results) == 0
