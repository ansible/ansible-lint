"""Assure samples produced desire outcomes."""
from ansiblelint.runner import Runner


def test_example(default_rules_collection):
    """example.yml is expected to have 15 match errors inside."""
    result = Runner(default_rules_collection, 'examples/example.yml', [], [], []).run()
    assert len(result) == 15


def test_example_plain_string(default_rules_collection):
    """Validates that loading valid YAML string produce error."""
    result = Runner(default_rules_collection, 'examples/plain_string.yml', [], [], []).run()
    assert len(result) == 1
    assert result[0].rule.id == "911"
    assert "A playbook must be a list of plays" in result[0].message
