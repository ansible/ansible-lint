import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.MetaMainHasInfoRule import MetaMainHasInfoRule

from . import RunFromText

NO_GALAXY_INFO = '''
author: the author
description: this meta/main.yml has no galaxy_info
'''

MISSING_INFO = '''
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
'''

BAD_TYPES = '''
galaxy_info:
  author: 007
  description: ['Testing meta']
  company: Not applicable

  license: MIT

  min_ansible_version: 2.5

  platforms: Fedora
'''

PLATFORMS_LIST_OF_STR = '''
galaxy_info:
  author: '007'
  description: 'Testing meta'
  company: Not applicable

  license: MIT

  min_ansible_version: 2.5

  platforms: ['Fedora', 'EL']
'''


class TestMetaMainHasInfo(unittest.TestCase):
    collection = RulesCollection()
    collection.register(MetaMainHasInfoRule())

    def setUp(self):
        self.runner = RunFromText(self.collection)

    def test_no_galaxy_info(self):
        results = self.runner.run_role_meta_main(NO_GALAXY_INFO)
        assert len(results) == 1
        self.assertIn("No 'galaxy_info' found",
                      str(results))

    def test_missing_info(self):
        results = self.runner.run_role_meta_main(MISSING_INFO)
        assert len(results) == 3
        self.assertIn("Role info should contain author",
                      str(results))
        self.assertIn("Role info should contain min_ansible_version",
                      str(results))
        self.assertIn("Platform should contain name",
                      str(results))

    def test_bad_types(self):
        results = self.runner.run_role_meta_main(BAD_TYPES)
        assert len(results) == 3
        self.assertIn("author should be a string", str(results))
        self.assertIn("description should be a string", str(results))
        self.assertIn("Platforms should be a list of dictionaries",
                      str(results))

    def test_platform_list_of_str(self):
        results = self.runner.run_role_meta_main(PLATFORMS_LIST_OF_STR)
        assert len(results) == 1
        self.assertIn("Platforms should be a list of dictionaries",
                      str(results))
