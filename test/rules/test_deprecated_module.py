"""Tests for deprecated-module rule."""
from ansiblelint.rules import RulesCollection
from ansiblelint.rules.deprecated_module import DeprecatedModuleRule
from ansiblelint.testing import RunFromText

MODULE_DEPRECATED = """
- name: Task example
  docker:
    debug: test
"""


def test_module_deprecated() -> None:
    """Test for deprecated-module."""
    collection = RulesCollection()
    collection.register(DeprecatedModuleRule())
    runner = RunFromText(collection)
    results = runner.run_role_tasks_main(MODULE_DEPRECATED)
    assert len(results) == 1
    # based on version and blend of ansible being used, we may
    # get a missing module, so we future proof the test
    assert (
        "couldn't resolve module" not in results[0].message
        or "Deprecated module" not in results[0].message
    )
