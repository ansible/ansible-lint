"""Assure samples produced desire outcomes."""
from ansiblelint.runner import Runner


def test_example(default_rules_collection):
    """example.yml is expected to have 15 match errors inside."""
    result = Runner(
        'examples/playbooks/example.yml',
        rules=default_rules_collection).run()
    assert len(result) == 15


def test_example_plain_string(default_rules_collection):
    """Validates that loading valid YAML string produce error."""
    result = Runner(
        'examples/playbooks/plain_string.yml',
        rules=default_rules_collection).run()
    assert len(result) >= 1
    passed = False
    for match in result:
        if match.rule.id == "911":
            passed = True
    assert passed, result


def test_example_custom_module(default_rules_collection):
    """custom_module.yml is expected to pass."""
    result = Runner(
        'examples/playbooks/custom_module.yml',
        rules=default_rules_collection).run()
    assert len(result) == 0
