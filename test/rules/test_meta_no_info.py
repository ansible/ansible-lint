"""Tests for meta-no-info rule."""
from ansiblelint.rules import RulesCollection
from ansiblelint.rules.meta_no_info import MetaMainHasInfoRule
from ansiblelint.testing import RunFromText

NO_GALAXY_INFO = """
author: the author
description: this meta/main.yml has no galaxy_info
"""

MISSING_INFO = """
galaxy_info:
  # author: the author
  description: Testing if meta contains values
  company: Not applicable

  license: MIT

  # min_ansible_version: 2.5

  platforms:
  - name: Fedora
    versions:
    - 25
  - missing_name: No name
    versions:
    - 25
"""

BAD_TYPES = """
galaxy_info:
  author: 007
  description: ['Testing meta']
  company: Not applicable

  license: MIT

  min_ansible_version: 2.5

  platforms: Fedora
"""

PLATFORMS_LIST_OF_STR = """
galaxy_info:
  author: '007'
  description: 'Testing meta'
  company: Not applicable

  license: MIT

  min_ansible_version: 2.5

  platforms: ['Fedora', 'EL']
"""


def test_no_galaxy_info() -> None:
    """Test meta-no-info with missing galaxy_info."""
    collection = RulesCollection()
    collection.register(MetaMainHasInfoRule())
    runner = RunFromText(collection)
    results = runner.run_role_meta_main(NO_GALAXY_INFO)
    assert len(results) == 1
    assert "No 'galaxy_info' found" in str(results)


def test_missing_info() -> None:
    """Test meta-no-info."""
    collection = RulesCollection()
    collection.register(MetaMainHasInfoRule())
    runner = RunFromText(collection)
    results = runner.run_role_meta_main(MISSING_INFO)
    assert len(results) == 3
    assert "Role info should contain author" in str(results)
    assert "Role info should contain min_ansible_version" in str(results)
    assert "Platform should contain name" in str(results)


def test_bad_types() -> None:
    """Test meta-no-info with bad types."""
    collection = RulesCollection()
    collection.register(MetaMainHasInfoRule())
    runner = RunFromText(collection)
    results = runner.run_role_meta_main(BAD_TYPES)
    assert len(results) == 3
    assert "author should be a string" in str(results)
    assert "description should be a string" in str(results)
    assert "Platforms should be a list of dictionaries" in str(results)


def test_platform_list_of_str() -> None:
    """Test meta-no-info with platforms."""
    collection = RulesCollection()
    collection.register(MetaMainHasInfoRule())
    runner = RunFromText(collection)
    results = runner.run_role_meta_main(PLATFORMS_LIST_OF_STR)
    assert len(results) == 1
    assert "Platforms should be a list of dictionaries" in str(results)
