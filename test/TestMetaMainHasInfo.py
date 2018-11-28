import unittest

from ansiblelint import RulesCollection
from ansiblelint.rules.MetaMainHasInfoRule import MetaMainHasInfoRule
from test import RunFromText

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


class TestMetaMainHasInfo(unittest.TestCase):
    collection = RulesCollection()
    collection.register(MetaMainHasInfoRule())

    def setUp(self):
        self.runner = RunFromText(self.collection)

    def test_no_galaxy_info(self):
        results = self.runner.run_role_meta_main(NO_GALAXY_INFO)
        self.assertIn("No 'galaxy_info' found",
                      str(results))

    def test_missing_info(self):
        results = self.runner.run_role_meta_main(MISSING_INFO)
        self.assertIn("Role info should contain author",
                      str(results))
        self.assertIn("Role info should contain min_ansible_version",
                      str(results))
        self.assertIn("Platform should contain name",
                      str(results))
