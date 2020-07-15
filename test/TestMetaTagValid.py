import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.MetaTagValidRule import MetaTagValidRule

from . import RunFromText

META_TAG_VALID = '''
galaxy_info:
  galaxy_tags: ['database', 'my s q l', 'MYTAG']
  categories: 'my_category_not_in_a_list'
'''


class TestMetaTagValid(unittest.TestCase):
    collection = RulesCollection()
    collection.register(MetaTagValidRule())

    def setUp(self):
        self.runner = RunFromText(self.collection)

    def test_valid_tag_rule(self):
        results = self.runner.run_role_meta_main(META_TAG_VALID)
        self.assertIn("Use 'galaxy_tags' rather than 'categories'",
                      str(results))
        self.assertIn("Expected 'categories' to be a list", str(results))
        self.assertIn("invalid: 'my s q l'", str(results))
        self.assertIn("invalid: 'MYTAG'", str(results))
