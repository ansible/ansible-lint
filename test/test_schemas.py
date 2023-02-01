"""Test schemas modules."""
import logging
import urllib
from time import sleep
from typing import Any
from unittest.mock import DEFAULT, MagicMock, patch

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
    (
        pytest.param(
            "examples/changelogs/changelog.yaml", ["schema[changelog]"], id="changelog"
        ),
    ),
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


def urlopen_side_effect(*_args: Any, **kwargs: Any) -> DEFAULT:
    """Actual test that timeout parameter is defined."""
    assert "timeout" in kwargs
    assert kwargs["timeout"] > 0
    return DEFAULT


@patch("urllib.request")
def test_requests_uses_timeout(mock_request: MagicMock) -> None:
    """Test that schema refresh uses timeout."""
    mock_request.urlopen.side_effect = urlopen_side_effect
    refresh_schemas(min_age_seconds=0)
    mock_request.urlopen.assert_called()


@patch("urllib.request")
def test_request_timeouterror_handling(
    mock_request: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that schema refresh can handle time out errors."""
    error_msg = "Simulating handshake operation time out."
    mock_request.urlopen.side_effect = urllib.error.URLError(TimeoutError(error_msg))
    with caplog.at_level(logging.DEBUG):
        assert refresh_schemas(min_age_seconds=0) == 1
    mock_request.urlopen.assert_called()
    assert "Skipped schema refresh due to unexpected exception: " in caplog.text
    assert error_msg in caplog.text
