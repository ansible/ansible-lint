"""Implementation of event-query rule for indirect node counting query validation."""

# Copyright (c) 2026, Ansible Project

from __future__ import annotations

import re
import sys
from typing import TYPE_CHECKING

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable

# Normalized taxonomy for device_type values.
# Collections should use one of these values to ensure consistent
# reporting across AAP node counting and audit systems.
VALID_DEVICE_TYPES = frozenset({
    # Compute
    "virtual_machine",
    "bare_metal",
    "container",
    # Networking
    "switch",
    "router",
    "firewall",
    "load_balancer",
    "access_point",
    # Cloud
    "cloud_instance",
    "cloud_service",
    "serverless_function",
    # Storage
    "storage_array",
    "storage_node",
    # Management / Control Plane
    "controller",
    "appliance",
    "management_server",
    # VMware-specific (normalized)
    "esxi_host",
    "vcenter_appliance",
    "cluster",
    "resource_pool",
    "datastore",
    # Organizational / Container
    "folder",
    "organizational_unit",
    # Generic
    "resource",
    "endpoint",
    "sensor",
})

# Module key must be a fully qualified collection name: namespace.collection.module
_FQCN_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*$")

# Tokenize strings and comments together with structural punctuation so braces
# and commas inside strings do not affect the static object checks.
_JQ_TOKENS = re.compile(r'"(?:\\.|[^"\\])*"|\#[^\n]*|[{}\[\](),:]|[^\s{}\[\](),:]+')
_MODULE_KEY_FORMAT = "event-query[module-key-format]"
_CANONICAL_FACTS_EMPTY = "event-query[canonical-facts-empty]"
_REQUIRED_OUTPUT_KEYS = ("name", "canonical_facts", "facts")
_REQUIRED_FIELD_PATTERNS = {
    field: re.compile(rf"\b{field}\s*:") for field in _REQUIRED_OUTPUT_KEYS
}


def _jq_tokens(text: str) -> list[str]:
    """Return static jq tokens, omitting comments."""
    return [token for token in _JQ_TOKENS.findall(text) if not token.startswith("#")]


def _extract_braced_block(text: str, keyword: str) -> str | None:
    """Extract a literal object, ignoring punctuation in strings and comments."""
    tokens = _jq_tokens(text)
    for index in range(len(tokens) - 2):
        if tokens[index : index + 3] != [keyword, ":", "{"]:
            continue
        depth = 1
        start = index + 3
        for end in range(start, len(tokens)):
            if tokens[end] == "{":
                depth += 1
            elif tokens[end] == "}":
                depth -= 1
                if depth == 0:
                    return " ".join(tokens[start:end])
    return None


def _object_fields(content: str) -> dict[str, str]:
    """Read top-level literal object fields without evaluating jq expressions."""
    fields = {}
    entry: list[str] = []
    depth = 0
    for token in [*_jq_tokens(content), ","]:
        if token == "," and depth == 0:
            if len(entry) >= 3 and entry[1] == ":":
                fields[entry[0].strip('"')] = " ".join(entry[2:])
            entry = []
            continue
        entry.append(token)
        if token in ("{", "[", "("):
            depth += 1
        elif token in ("}", "]", ")"):
            depth -= 1
    return fields


class EventQueryRule(AnsibleLintRule):
    """Validate indirect node counting event_query.yml files."""

    id = "event-query"
    description = (
        "Performs static pattern checks on extensions/audit/event_query.yml "
        "for AAP indirect node counting. Checks module key "
        "format (FQCN), required output fields (name, canonical_facts, facts), "
        "and normalized device_type taxonomy."
    )
    severity = "HIGH"
    tags = ["metadata", "aap"]
    version_changed = "26.9.0"
    _ids = {
        _MODULE_KEY_FORMAT: "Module key must be a fully qualified collection name (namespace.collection.module).",
        "event-query[invalid-entry]": "Each module entry must be a mapping.",
        "event-query[invalid-query-type]": "The query field must be a string.",
        "event-query[missing-query]": "Each module entry must have a 'query' field.",
        "event-query[query-missing-field]": "Query output must produce 'name', 'canonical_facts', and 'facts' fields.",
        "event-query[device-type]": "facts.device_type should use a value from the normalized taxonomy.",
        "event-query[device-type-missing]": "facts section in query output should include a 'device_type' field.",
        _CANONICAL_FACTS_EMPTY: "canonical_facts must define at least one unique identifier field.",
    }

    def _validate_device_type(
        self,
        module_key: str,
        query: str,
        file: Lintable,
    ) -> list[MatchError]:
        """Validate device_type field in facts section of query output."""
        facts_content = _extract_braced_block(query, "facts")
        fields = _object_fields(facts_content) if facts_content is not None else {}
        if "device_type" not in fields:
            return [
                self.create_matcherror(
                    message=f"Module '{module_key}' query output should include 'device_type' in the facts section.",
                    tag="event-query[device-type-missing]",
                    filename=file,
                ),
            ]

        device_type = fields["device_type"]
        if device_type not in {f'"{value}"' for value in VALID_DEVICE_TYPES}:
            return [
                self.create_matcherror(
                    message=(
                        f"Module '{module_key}' uses device_type '{device_type}' "
                        f"which must be a quoted literal from the normalized taxonomy. "
                        f"Valid types include: virtual_machine, bare_metal, container, "
                        f"switch, router, firewall, cloud_instance, esxi_host, "
                        f"vcenter_appliance, cluster, resource, endpoint. "
                        f"See event_query.md for the full list."
                    ),
                    tag="event-query[device-type]",
                    filename=file,
                ),
            ]

        return []

    def _validate_canonical_facts(
        self,
        module_key: str,
        query: str,
        file: Lintable,
    ) -> list[MatchError]:
        """Validate canonical_facts field in query output."""
        cf_content = _extract_braced_block(query, "canonical_facts")
        if cf_content is not None:
            non_null_fields = [
                value
                for value in _object_fields(cf_content).values()
                if value != "null"
            ]
            if not non_null_fields:
                return [
                    self.create_matcherror(
                        message=f"Module '{module_key}' canonical_facts must define at least one non-null unique identifier.",
                        tag=_CANONICAL_FACTS_EMPTY,
                        filename=file,
                    ),
                ]
        elif _REQUIRED_FIELD_PATTERNS["canonical_facts"].search(query):
            return [
                self.create_matcherror(
                    message=f"Module '{module_key}' canonical_facts must be an object with at least one unique identifier field.",
                    tag=_CANONICAL_FACTS_EMPTY,
                    filename=file,
                ),
            ]

        return []

    @staticmethod
    def _is_event_query_file(file: Lintable) -> bool:
        """Check whether the file is in an extensions/audit directory."""
        if file.path.name != "event_query.yml":
            return False
        parts = file.path.parts
        try:
            ext_idx = parts.index("extensions")
            return parts[ext_idx + 1] == "audit"
        except (ValueError, IndexError):
            return False

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        """Validate event_query.yml files."""
        if not self._is_event_query_file(file):
            return []

        results: list[MatchError] = []
        data = file.data

        if not isinstance(data, dict):
            return results

        for module_key, entry in data.items():
            if not isinstance(module_key, str):
                results.append(
                    self.create_matcherror(
                        message=f"Module key '{module_key}' is not a valid FQCN. Expected format: namespace.collection.module_name",
                        tag=_MODULE_KEY_FORMAT,
                        filename=file,
                    ),
                )
                continue
            if module_key.startswith("__"):
                continue

            if not _FQCN_PATTERN.match(module_key):
                results.append(
                    self.create_matcherror(
                        message=f"Module key '{module_key}' is not a valid FQCN. Expected format: namespace.collection.module_name",
                        tag=_MODULE_KEY_FORMAT,
                        filename=file,
                    ),
                )

            if not isinstance(entry, dict):
                results.append(
                    self.create_matcherror(
                        message=f"Module '{module_key}' entry must be a mapping.",
                        tag="event-query[invalid-entry]",
                        filename=file,
                    )
                )
                continue

            query = entry.get("query")
            if "query" not in entry or (isinstance(query, str) and not query):
                results.append(
                    self.create_matcherror(
                        message=f"Module '{module_key}' is missing required 'query' field.",
                        tag="event-query[missing-query]",
                        filename=file,
                    ),
                )
                continue

            if not isinstance(query, str):
                results.append(
                    self.create_matcherror(
                        message=f"Module '{module_key}' query must be a string.",
                        tag="event-query[invalid-query-type]",
                        filename=file,
                    )
                )
                continue

            results.extend(
                self.create_matcherror(
                    message=f"Module '{module_key}' query output is missing required field '{field}'.",
                    tag="event-query[query-missing-field]",
                    filename=file,
                )
                for field in _REQUIRED_OUTPUT_KEYS
                if not _REQUIRED_FIELD_PATTERNS[field].search(query)
            )

            results.extend(self._validate_canonical_facts(module_key, query, file))
            results.extend(self._validate_device_type(module_key, query, file))

        return results


if "pytest" in sys.modules:
    import pytest

    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    @pytest.mark.parametrize(
        ("file", "expected"),
        (
            pytest.param(
                "examples/event_query/pass/extensions/audit/event_query.yml",
                [],
                id="pass",
            ),
            pytest.param(
                "examples/event_query/fail_bad_fqcn/extensions/audit/event_query.yml",
                [_MODULE_KEY_FORMAT],
                id="bad-fqcn",
            ),
            pytest.param(
                "examples/event_query/fail_missing_query/extensions/audit/event_query.yml",
                ["event-query[missing-query]"],
                id="missing-query",
            ),
            pytest.param(
                "examples/event_query/fail_missing_fields/extensions/audit/event_query.yml",
                ["event-query[query-missing-field]"],
                id="missing-fields",
            ),
            pytest.param(
                "examples/event_query/fail_bad_device_type/extensions/audit/event_query.yml",
                ["event-query[device-type]"],
                id="bad-device-type",
            ),
            pytest.param(
                "examples/event_query/fail_non_string_key/extensions/audit/event_query.yml",
                [_MODULE_KEY_FORMAT],
                id="non-string-key",
            ),
            pytest.param(
                "examples/event_query/fail_null_canonical_facts/extensions/audit/event_query.yml",
                [
                    _CANONICAL_FACTS_EMPTY,
                    "event-query[device-type-missing]",
                ],
                id="null-canonical-facts",
            ),
            pytest.param(
                "examples/event_query/fail_scalar_canonical_facts/extensions/audit/event_query.yml",
                [_CANONICAL_FACTS_EMPTY],
                id="scalar-canonical-facts",
            ),
            pytest.param(
                "examples/event_query/fail_non_dict_entry/extensions/audit/event_query.yml",
                ["event-query[invalid-entry]"] * 2,
                id="non-dict-entry",
            ),
            pytest.param(
                "examples/event_query/fail_non_string_query/extensions/audit/event_query.yml",
                ["event-query[invalid-query-type]"],
                id="non-string-query",
            ),
        ),
    )
    def test_event_query_rule(
        default_rules_collection: RulesCollection,
        file: str,
        expected: list[str],
    ) -> None:
        """Validate event-query rule works as intended."""
        results = Runner(file, rules=default_rules_collection).run()

        event_query_results = [r for r in results if r.tag.startswith("event-query")]
        assert len(event_query_results) == len(expected)
        for index, result in enumerate(event_query_results):
            assert result.tag == expected[index]

    @pytest.mark.parametrize("query", (None, [], {}, 0, False, ["jq"]))
    def test_invalid_query_type(query: object) -> None:
        """Reject non-string queries, including empty containers, zero, and False."""
        import json

        from ansiblelint.file_utils import Lintable

        lintable = Lintable(
            "extensions/audit/event_query.yml",
            content=json.dumps({"example.collection.module": {"query": query}}),
        )
        assert [match.tag for match in EventQueryRule().matchyaml(lintable)] == [
            "event-query[invalid-query-type]",
        ]

    @pytest.mark.parametrize(
        ("value", "valid"),
        (
            ('"cluster"', True),
            ('("cluster")', False),
            ("$data.type", False),
            ("cluster", False),
            ('"cluster" + "invalid"', False),
        ),
    )
    def test_device_type_literal(value: str, valid: bool) -> None:
        """Only a complete taxonomy literal satisfies static validation."""
        from ansiblelint.file_utils import Lintable

        matches = EventQueryRule()._validate_device_type(  # ruff: ignore[private-member-access]
            "example.collection.module",
            f"facts: {{ device_type: {value} }}",
            Lintable("extensions/audit/event_query.yml", content="---\n"),
        )
        assert (not matches) == valid

    @pytest.mark.parametrize(
        ("content", "valid"),
        (
            ("sid: ($data.sid // null)", True),
            ('sid: "null,}:value"', True),
            ('sid: {value: "a,b"}', True),
            ("sid: null, guid: null", False),
            ("", False),
        ),
    )
    def test_canonical_fact_expressions(content: str, valid: bool) -> None:
        """Nested expressions and string punctuation do not split fields."""
        from ansiblelint.file_utils import Lintable

        matches = EventQueryRule()._validate_canonical_facts(  # ruff: ignore[private-member-access]
            "example.collection.module",
            f"canonical_facts: {{ {content} }}",
            Lintable("extensions/audit/event_query.yml", content="---\n"),
        )
        assert (not matches) == valid
