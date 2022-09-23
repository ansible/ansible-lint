"""Tests related to inclusions."""
import pytest
from _pytest.logging import LogCaptureFixture

from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner


def test_cases_warning_message(default_rules_collection: RulesCollection) -> None:
    """Test that including a non-existing file produces an error."""
    playbook_path = "examples/playbooks/play_miss_include.yml"
    runner = Runner(playbook_path, rules=default_rules_collection)
    results = runner.run()

    assert len(runner.lintables) == 3
    assert len(results) == 1
    assert "No such file or directory" in results[0].message


@pytest.mark.parametrize(
    "playbook_path",
    (
        pytest.param("examples/playbooks/test_include_inplace.yml", id="inplace"),
        pytest.param("examples/playbooks/test_include_relative.yml", id="relative"),
    ),
)
def test_cases_that_do_not_report(
    playbook_path: str,
    default_rules_collection: RulesCollection,
    caplog: LogCaptureFixture,
) -> None:
    """Test that relative inclusions are properly followed."""
    runner = Runner(playbook_path, rules=default_rules_collection)
    result = runner.run()
    noexist_message_count = 0

    for record in caplog.records:
        for msg in ("No such file or directory", "Couldn't open"):
            if msg in str(record):
                noexist_message_count += 1

    assert noexist_message_count == 0
    assert len(result) == 0
