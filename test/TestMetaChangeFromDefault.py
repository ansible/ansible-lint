# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.MetaChangeFromDefaultRule import MetaChangeFromDefaultRule
from ansiblelint.testing import RunFromText

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

    def setUp(self) -> None:
        self.runner = RunFromText(self.collection)

    def test_default_galaxy_info(self) -> None:
        results = self.runner.run_role_meta_main(DEFAULT_GALAXY_INFO)
        assert "Should change default metadata: author" in str(results)
        assert "Should change default metadata: description" in str(results)
        assert "Should change default metadata: company" in str(results)
        assert "Should change default metadata: license" in str(results)
