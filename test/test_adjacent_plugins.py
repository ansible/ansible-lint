"""Test ability to recognize adjacent modules/plugins."""

import logging

import pytest

from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner


def test_adj_action(
    default_rules_collection: RulesCollection,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Assures local collections are found."""
    playbook_path = "examples/playbooks/adj_action.yml"

    with caplog.at_level(logging.DEBUG):
        runner = Runner(playbook_path, rules=default_rules_collection, verbosity=1)
        results = runner.run()
    assert "Unable to load module" not in caplog.text
    assert "Unable to resolve FQCN" not in caplog.text

    assert len(runner.lintables) == 1
    assert len(results) == 0
