"""Assure samples produced desire outcomes."""
from ansiblelint.runner import Runner


def test_example(default_rules_collection):
    """example.yml is expected to have 5 match errors inside."""
    result = Runner(default_rules_collection, 'examples/example.yml', [], [], []).run()
    assert len(result) == 5
