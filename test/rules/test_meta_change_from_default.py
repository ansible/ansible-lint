"""Tests for meta-incorrect rule."""
from ansiblelint.rules import RulesCollection
from ansiblelint.rules.meta_incorrect import MetaChangeFromDefaultRule
from ansiblelint.testing import RunFromText

DEFAULT_GALAXY_INFO = """
galaxy_info:
  author: your name
  description: your description
  company: your company (optional)
  license: license (GPLv2, CC-BY, etc)
"""


def test_default_galaxy_info() -> None:
    """Test for meta-incorrect."""
    collection = RulesCollection()
    collection.register(MetaChangeFromDefaultRule())
    runner = RunFromText(collection)
    results = runner.run_role_meta_main(DEFAULT_GALAXY_INFO)
    # Disabled check because default value is not passing schema validation
    # assert "Should change default metadata: author" in str(results)
    assert "Should change default metadata: description" in str(results)
    assert "Should change default metadata: company" in str(results)
    assert "Should change default metadata: license" in str(results)
