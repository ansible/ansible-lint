"""Test playbooks with local content."""
from ansiblelint.runner import Runner


def test_local_collection(default_rules_collection):
    """Assures local collections are found."""
    playbook_path = 'test/local-content/test-collection.yml'
    runner = Runner(default_rules_collection, playbook_path, [], [], [])
    results = runner.run()

    assert len(runner.playbooks) == 1
    assert len(results) == 0


def test_roles_local_content(default_rules_collection):
    """Assures local content in roles is found."""
    playbook_path = 'test/local-content/test-roles-success/test.yml'
    runner = Runner(default_rules_collection, playbook_path, [], [], [])
    results = runner.run()

    assert len(runner.playbooks) == 4
    assert len(results) == 0


def test_roles_local_content_failure(default_rules_collection):
    """Assures local content in roles is found, even if Ansible itself has trouble."""
    playbook_path = 'test/local-content/test-roles-failed/test.yml'
    runner = Runner(default_rules_collection, playbook_path, [], [], [])
    results = runner.run()

    assert len(runner.playbooks) == 4
    assert len(results) == 0


def test_roles_local_content_failure_complete(default_rules_collection):
    """Role with local content that is not found."""
    playbook_path = 'test/local-content/test-roles-failed-complete/test.yml'
    runner = Runner(default_rules_collection, playbook_path, [], [], [])
    x = runner.run()
    assert len(x) == 1
    assert "couldn't resolve module" in x[0].message
