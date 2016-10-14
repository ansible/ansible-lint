import unittest
from ansiblelint import Runner, RulesCollection
from ansiblelint.rules.OctalPermissionsRule import OctalPermissionsRule


class TestOctalPermissionsRuleWithFile(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(OctalPermissionsRule())

    def test_file_positive(self):
        success = 'test/octalpermissions-success.yml'
        good_runner = Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

    def test_file_negative(self):
        failure = 'test/octalpermissions-failure.yml'
        bad_runner = Runner(self.collection, failure, [], [], [])
        errs = bad_runner.run()
        self.assertEqual(4, len(errs))
