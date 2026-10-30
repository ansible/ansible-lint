"""Tests for event-query rule edge cases."""

from pathlib import Path

import pytest

from ansiblelint.file_utils import Lintable
from ansiblelint.rules.event_query import EventQueryRule


@pytest.mark.parametrize(
    ("path", "content", "expected"),
    (
        pytest.param("extensions/audit/other.yml", "{}", [], id="other-file"),
        pytest.param(
            "extensions/other/event_query.yml", "{}", [], id="other-extension"
        ),
        pytest.param("event_query.yml", "{}", [], id="no-extensions-directory"),
        pytest.param(
            "extensions/audit/event_query.yml",
            "example.collection.module:\n  query: \"{name: .name, canonical_facts: {}, facts: {device_type: 'router'}}\"\n",
            ["event-query[canonical-facts-empty]"],
            id="empty-canonical-facts",
        ),
        pytest.param(
            "extensions/audit/event_query.yml",
            'example.collection.module:\n  query: "{name: .name, canonical_facts: {id: .id"\n',
            [
                "event-query[canonical-facts-empty]",
                "event-query[device-type-missing]",
                "event-query[query-missing-field]",
            ],
            id="unclosed-canonical-facts",
        ),
    ),
)
def test_event_query_edge_cases(
    tmp_path: Path, path: str, content: str, expected: list[str]
) -> None:
    """Check path filtering and malformed or empty query output."""
    target = tmp_path / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    matches = EventQueryRule().matchyaml(Lintable(target))
    assert sorted(match.tag for match in matches) == sorted(expected)
