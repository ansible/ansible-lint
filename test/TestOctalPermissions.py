import unittest
from ansiblelint import Runner, RulesCollection
from ansiblelint.rules.OctalPermissionsRule import OctalPermissionsRule


class TestOctalPermissionsRuleWithFile(unittest.TestCase):
    collection = RulesCollection()
    VALID_MODES = [ 0777, 0775, 0770, 0755, 0750, 0711, 0710, 0700,
                    0666, 0664, 0660, 0644, 0640, 0600,
                    0555, 0551, 0550, 0511, 0510, 0500,
                    0444, 0440, 0400 ]

    INVALID_MODES = [ 777, 775, 770, 755, 750, 711, 710, 700,
                    666, 664, 660, 644, 640, 622, 620, 600,
                    555, 551, 550, # 511 == 0777, 510 == 0776, 500 == 0764
                    444, 440, 400 ]

    def setUp(self):
        self.rule = OctalPermissionsRule()
        self.collection.register(self.rule)

    def test_file_positive(self):
        success = 'test/octalpermissions-success.yml'
        good_runner = Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

    def test_file_negative(self):
        failure = 'test/octalpermissions-failure.yml'
        bad_runner = Runner(self.collection, failure, [], [], [])
        errs = bad_runner.run()
        self.assertEqual(5, len(errs))

    def test_valid_modes(self):
        for mode in self.VALID_MODES:
            self.assertFalse(self.rule.is_invalid_permission(mode), msg="0%o should be a valid mode" % mode)

    def test_invalid_modes(self):
        for mode in self.INVALID_MODES:
            self.assertTrue(self.rule.is_invalid_permission(mode), msg="%d should be an invalid mode" % mode)
