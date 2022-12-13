"""Test schemas modules."""
from time import sleep

import pytest

from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner
from ansiblelint.schemas import refresh_schemas


def test_refresh_schemas() -> None:
    """Test for schema update skip."""
    # This is written as a single test in order to avoid concurrency issues,
    # which caused random issues on CI when the two tests run in parallel
    # and or in different order.
    assert refresh_schemas(min_age_seconds=3600 * 24 * 365 * 10) == 0
    sleep(1)
    # this should disable the cache and force an update
    assert refresh_schemas(min_age_seconds=0) == 1
    sleep(1)
    # should be cached now
    assert refresh_schemas(min_age_seconds=10) == 0


@pytest.mark.parametrize(
    ("file", "expected_tags"),
    (pytest.param("examples/changelog.yml", ["schema[changelog]"], id="changelog"),),
)
def test_schema(
    default_rules_collection: RulesCollection,
    file: str,
    expected_tags: list[str],
) -> None:
    """Test that runner can go through any corner cases."""
    runner = Runner(file, rules=default_rules_collection)
    matches = runner.run()

    assert len(matches) == len(expected_tags)
    for i, match in enumerate(matches):
        assert match.tag == expected_tags[i]
