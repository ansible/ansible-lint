"""Generic tests for AnsibleLintRule class."""

from __future__ import annotations

from typing import Any

import pytest

from ansiblelint.constants import SKIPPED_RULES_KEY
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule, RulesCollection, _should_skip_play
from ansiblelint.rules.complexity import ComplexityRule


def test_unjinja() -> None:
    """Verify that unjinja understands nested mustache."""
    text = "{{ a }} {% b %} {# try to confuse parsing inside a comment { {{}} } #}"
    output = "JINJA_EXPRESSION JINJA_STATEMENT JINJA_COMMENT"
    assert AnsibleLintRule.unjinja(text) == output


def test_should_skip_play() -> None:
    """Play skip helpers honor skipped-rules metadata and tags."""
    assert _should_skip_play(None, "fqcn") is True
    assert _should_skip_play({SKIPPED_RULES_KEY: ["fqcn"]}, "fqcn") is True
    assert _should_skip_play({"tags": ["skip_ansible_lint"]}, "fqcn") is True
    assert _should_skip_play({"tags": ["other"]}, "fqcn") is False


def test_yaml_string_load_failure_branches(
    empty_rule_collection: RulesCollection,
) -> None:
    """String yaml data should short-circuit matchyaml load failures."""
    rule = ComplexityRule()
    empty_rule_collection.register(rule)

    parsed = Lintable("x.yml", content="---\n")
    parsed.state = [{"hosts": "all"}]
    assert rule._yaml_string_load_failure(parsed) is None  # noqa: SLF001

    vault = Lintable("v.yml", content="")
    vault.state = "$ANSIBLE_VAULT;1.1;AES256\n0000"
    assert rule._yaml_string_load_failure(vault) == []  # noqa: SLF001

    broken = Lintable("b.yml", content="")
    broken.state = "not-yaml-structure"
    matches = rule._yaml_string_load_failure(broken)  # noqa: SLF001
    assert matches is not None
    assert matches[0].rule.id == "load-failure"


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
    empty_rule_collection: RulesCollection,
) -> None:
    """Check that a rule config can be accessed."""
    empty_rule_collection.register(ComplexityRule())

    for rule in empty_rule_collection:
        if rule.id == rule_name:
            assert rule._collection  # noqa: SLF001
            assert rule.rule_config == rule_config
