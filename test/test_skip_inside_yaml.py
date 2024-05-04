"""Tests related to use of inline noqa."""

import pytest

from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner
from ansiblelint.testing import run_ansible_lint


def test_role_tasks_with_block(default_rules_collection: RulesCollection) -> None:
    """Check that blocks in role tasks can contain skips."""
    results = Runner(
        "examples/playbooks/roles/fixture_1",
        rules=default_rules_collection,
    ).run()
    assert len(results) == 4
    for result in results:
        assert result.tag == "latest[git]"


@pytest.mark.parametrize(
    ("lintable", "expected"),
    (pytest.param("examples/playbooks/test_skip_inside_yaml.yml", 4, id="yaml"),),
)
def test_inline_skips(
    default_rules_collection: RulesCollection,
    lintable: str,
    expected: int,
) -> None:
    """Check that playbooks can contain skips."""
    results = Runner(lintable, rules=default_rules_collection).run()

    assert len(results) == expected


def test_role_meta() -> None:
    """Test running from inside meta folder."""
    role_path = "examples/roles/meta_noqa"

    result = run_ansible_lint("-v", role_path)
    assert len(result.stdout) == 0
    assert result.returncode == 0
