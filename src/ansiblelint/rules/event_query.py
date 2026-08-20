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

# Required keys in the jq query output object
_REQUIRED_OUTPUT_KEYS = {"name", "canonical_facts", "facts"}


def _extract_braced_block(text: str, keyword: str) -> str | None:
    """Extract content between braces after 'keyword: {', handling nesting."""
    pattern = re.compile(rf"\b{keyword}\s*:\s*\{{")
    m = pattern.search(text)
    if not m:
        return None
    depth = 1
    start = m.end()
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i]
    return None


class EventQueryRule(AnsibleLintRule):
    """Validate indirect node counting event_query.yml files."""

    id = "event-query"
    description = (
        "Validates that extensions/audit/event_query.yml files follow the "
        "required schema for AAP indirect node counting. Checks module key "
        "format (FQCN), required output fields (name, canonical_facts, facts), "
        "and normalized device_type taxonomy."
    )
    severity = "HIGH"
    tags = ["metadata", "aap"]
    version_changed = "26.9.0"
    _ids = {
        "event-query[module-key-format]": "Module key must be a fully qualified collection name (namespace.collection.module).",
        "event-query[missing-query]": "Each module entry must have a 'query' field.",
        "event-query[query-missing-field]": "Query output must produce 'name', 'canonical_facts', and 'facts' fields.",
        "event-query[device-type]": "facts.device_type should use a value from the normalized taxonomy.",
        "event-query[device-type-missing]": "facts section in query output should include a 'device_type' field.",
        "event-query[canonical-facts-empty]": "canonical_facts must define at least one unique identifier field.",
    }

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        """Validate event_query.yml files."""
        if file.path.name != "event_query.yml":
            return []

        parts = file.path.parts
        try:
            ext_idx = parts.index("extensions")
            if parts[ext_idx + 1] != "audit":
                return []
        except (ValueError, IndexError):
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
                        tag="event-query[module-key-format]",
                        filename=file,
                    ),
                )
                continue
            if module_key.startswith("__"):
                continue

            # Check module key is valid FQCN
            if not _FQCN_PATTERN.match(module_key):
                results.append(
                    self.create_matcherror(
                        message=f"Module key '{module_key}' is not a valid FQCN. Expected format: namespace.collection.module_name",
                        tag="event-query[module-key-format]",
                        filename=file,
                    ),
                )

            if not isinstance(entry, dict):
                continue

            # Check 'query' field exists
            query = entry.get("query")
            if not query:
                results.append(
                    self.create_matcherror(
                        message=f"Module '{module_key}' is missing required 'query' field.",
                        tag="event-query[missing-query]",
                        filename=file,
                    ),
                )
                continue

            if not isinstance(query, str):
                continue

            # Validate query output contains required fields
            results.extend(
                self.create_matcherror(
                    message=f"Module '{module_key}' query output is missing required field '{field}'.",
                    tag="event-query[query-missing-field]",
                    filename=file,
                )
                for field in _REQUIRED_OUTPUT_KEYS
                if not re.search(rf"\b{field}\s*:", query)
            )

            facts_content = _extract_braced_block(query, "facts")
            if facts_content is not None:
                if "device_type" not in facts_content:
                    results.append(
                        self.create_matcherror(
                            message=f"Module '{module_key}' query output should include 'device_type' in the facts section.",
                            tag="event-query[device-type-missing]",
                            filename=file,
                        ),
                    )
                else:
                    dt_match = re.search(
                        r'device_type\s*:\s*["\']([^"\']+)["\']',
                        facts_content,
                    )
                    if dt_match:
                        device_type = dt_match.group(1)
                        if device_type not in VALID_DEVICE_TYPES:
                            results.append(
                                self.create_matcherror(
                                    message=(
                                        f"Module '{module_key}' uses device_type '{device_type}' "
                                        f"which is not in the normalized taxonomy. "
                                        f"Valid types include: virtual_machine, bare_metal, container, "
                                        f"switch, router, firewall, cloud_instance, esxi_host, "
                                        f"vcenter_appliance, cluster, resource, endpoint. "
                                        f"See event_query.md for the full list."
                                    ),
                                    tag="event-query[device-type]",
                                    filename=file,
                                ),
                            )
            else:
                results.append(
                    self.create_matcherror(
                        message=f"Module '{module_key}' query output should include 'device_type' in the facts section.",
                        tag="event-query[device-type-missing]",
                        filename=file,
                    ),
                )

            if re.search(r"canonical_facts\s*:\s*null\b", query):
                results.append(
                    self.create_matcherror(
                        message=f"Module '{module_key}' canonical_facts must define at least one non-null unique identifier.",
                        tag="event-query[canonical-facts-empty]",
                        filename=file,
                    ),
                )
            else:
                cf_content = _extract_braced_block(query, "canonical_facts")
                if cf_content is not None:
                    non_null_fields = [
                        line.strip()
                        for line in cf_content.split(",")
                        if line.strip() and "null" not in line.split(":")[-1]
                    ]
                    if not non_null_fields:
                        results.append(
                            self.create_matcherror(
                                message=f"Module '{module_key}' canonical_facts must define at least one non-null unique identifier.",
                                tag="event-query[canonical-facts-empty]",
                                filename=file,
                            ),
                        )
                elif re.search(r"canonical_facts\s*:", query):
                    results.append(
                        self.create_matcherror(
                            message=f"Module '{module_key}' canonical_facts must be an object with at least one unique identifier field.",
                            tag="event-query[canonical-facts-empty]",
                            filename=file,
                        ),
                    )

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
                ["event-query[module-key-format]"],
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
                ["event-query[module-key-format]"],
                id="non-string-key",
            ),
            pytest.param(
                "examples/event_query/fail_null_canonical_facts/extensions/audit/event_query.yml",
                [
                    "event-query[device-type-missing]",
                    "event-query[canonical-facts-empty]",
                ],
                id="null-canonical-facts",
            ),
            pytest.param(
                "examples/event_query/fail_scalar_canonical_facts/extensions/audit/event_query.yml",
                ["event-query[canonical-facts-empty]"],
                id="scalar-canonical-facts",
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
