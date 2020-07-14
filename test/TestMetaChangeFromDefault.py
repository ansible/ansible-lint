import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.MetaChangeFromDefaultRule import MetaChangeFromDefaultRule

from . import RunFromText

DEFAULT_GALAXY_INFO = '''
galaxy_info:
  author: your name
  description: your description
  company: your company (optional)
  license: license (GPLv2, CC-BY, etc)
'''


class TestMetaChangeFromDefault(unittest.TestCase):
    collection = RulesCollection()
    collection.register(MetaChangeFromDefaultRule())

    def setUp(self):
        self.runner = RunFromText(self.collection)

    def test_default_galaxy_info(self):
        results = self.runner.run_role_meta_main(DEFAULT_GALAXY_INFO)
        self.assertIn("Should change default metadata: author",
                      str(results))
        self.assertIn("Should change default metadata: description",
                      str(results))
        self.assertIn("Should change default metadata: company",
                      str(results))
        self.assertIn("Should change default metadata: license",
                      str(results))
