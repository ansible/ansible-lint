from typing import Any, Dict

import pytest
from _pytest.monkeypatch import MonkeyPatch

from ansiblelint.config import options
from ansiblelint.rules import AnsibleLintRule


def test_unjinja() -> None:
    """Verify that unjinja understands nested mustache."""
    text = "{{ a }} {% b %} {# try to confuse parsing inside a comment { {{}} } #}"
    output = "JINJA_EXPRESSION JINJA_STATEMENT JINJA_COMMENT"
    assert AnsibleLintRule.unjinja(text) == output


@pytest.mark.parametrize('rule_config', (dict(), dict(foo=True, bar=1)))
def test_rule_config(rule_config: Dict[str, Any], monkeypatch: MonkeyPatch) -> None:
    """Check that a rule config is inherited from options."""
    rule_id = 'rule-0'
    monkeypatch.setattr(AnsibleLintRule, 'id', rule_id)
    monkeypatch.setitem(options.rules, rule_id, rule_config)

    rule = AnsibleLintRule()
    assert set(rule.rule_config.items()) == set(rule_config.items())
    assert all(rule.get_config(k) == v for k, v in rule_config.items())
