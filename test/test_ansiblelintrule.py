"""Generic tests for AnsibleLintRule class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from ansiblelint.rules import AnsibleLintRule, RulesCollection

if TYPE_CHECKING:
    from ansiblelint.config import Options


def test_unjinja() -> None:
    """Verify that unjinja understands nested mustache."""
    text = "{{ a }} {% b %} {# try to confuse parsing inside a comment { {{}} } #}"
    output = "JINJA_EXPRESSION JINJA_STATEMENT JINJA_COMMENT"
    assert AnsibleLintRule.unjinja(text) == output


@pytest.mark.parametrize("rule_config", ({}, {"foo": True, "bar": 1}))
def test_rule_config(
    rule_config: dict[str, Any],
    config_options: Options,
) -> None:
    """Check that a rule config can be accessed."""
    config_options.rules["load-failure"] = rule_config
    rules = RulesCollection(options=config_options)
    for rule in rules:
        if rule.id == "load-failure":
            assert rule._collection  # noqa: SLF001
            assert rule.rule_config == rule_config
