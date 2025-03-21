"""Generic tests for AnsibleLintRule class."""

from __future__ import annotations

from typing import Any

import pytest

from ansiblelint.rules import AnsibleLintRule, RulesCollection
from ansiblelint.rules.complexity import ComplexityRule


def test_unjinja() -> None:
    """Verify that unjinja understands nested mustache."""
    text = "{{ a }} {% b %} {# try to confuse parsing inside a comment { {{}} } #}"
    output = "JINJA_EXPRESSION JINJA_STATEMENT JINJA_COMMENT"
    assert AnsibleLintRule.unjinja(text) == output


@pytest.mark.parametrize(
    ("rule_name", "rule_config"),
    (
        pytest.param("load-failure", {}, id="load-failure"),
        pytest.param("complexity", {}, id="complexity"),
    ),
)
def test_rule_config(
    rule_name: str,
    rule_config: dict[str, Any],
) -> None:
    """Check that a rule config can be accessed."""
    rules = RulesCollection()
    rules.register(ComplexityRule())

    for rule in rules:
        if rule.id == rule_name:
            assert rule._collection  # noqa: SLF001
            assert rule.rule_config == rule_config
