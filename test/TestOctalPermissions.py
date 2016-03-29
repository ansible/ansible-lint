import unittest
import ansiblelint.utils
from itertools import product  # Cartesian product: all subsets of length n
from ansiblelint import RulesCollection
from ansiblelint.rules.OctalPermissionsRule import OctalPermissionsRule


class TestOctalPermissionsRuleWithFile(unittest.TestCase):
    collection = RulesCollection()

    def test_file_positive(self):
        self.collection.register(OctalPermissionsRule())
        success = 'test/octalpermissions-success.yml'
        good_runner = ansiblelint.Runner(self.collection, [success], [], [], [])
        self.assertEqual([], good_runner.run())

    def test_file_negative(self):
        self.collection.register(OctalPermissionsRule())
        failure = 'test/octalpermissions-failure.yml'
        bad_runner = ansiblelint.Runner(self.collection, [failure], [], [], [])
        errs = bad_runner.run()
        self.assertEqual(4, len(errs))
