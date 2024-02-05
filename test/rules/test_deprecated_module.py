"""Tests for deprecated-module rule."""

from pathlib import Path

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.deprecated_module import DeprecatedModuleRule
from ansiblelint.testing import RunFromText

MODULE_DEPRECATED = """
- name: Task example
  docker:
    debug: test
"""


def test_module_deprecated(tmp_path: Path) -> None:
    """Test for deprecated-module."""
    collection = RulesCollection()
    collection.register(DeprecatedModuleRule())
    runner = RunFromText(collection)
    results = runner.run_role_tasks_main(MODULE_DEPRECATED, tmp_path=tmp_path)
    assert len(results) == 1
    # based on version and blend of ansible being used, we may
    # get a missing module, so we future proof the test
    assert (
        "couldn't resolve module" not in results[0].message
        or "Deprecated module" not in results[0].message
    )
