import unittest
import ansiblelint.utils
from ansiblelint import RulesCollection
from ansiblelint.rules.FailOnDuplicateKeysRule import FailOnDuplicateKeysRule
from yaml.constructor import ConstructorError


class TestFailOnDuplicateKeysRule(unittest.TestCase):
    collection = RulesCollection()

    def test_fail_on_duplicate_keys(self):
        self.collection.register(FailOnDuplicateKeysRule())
        success = 'test/fail-on-duplicate-keys.yml'
        with self.assertRaises(ConstructorError):
            good_runner = ansiblelint.Runner(self.collection, success, [], [], [])
            self.assertEqual([], good_runner.run())
