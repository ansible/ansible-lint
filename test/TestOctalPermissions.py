import unittest
from ansiblelint import Runner, RulesCollection
from ansiblelint.rules.OctalPermissionsRule import OctalPermissionsRule


class TestOctalPermissionsRuleWithFile(unittest.TestCase):

    collection = RulesCollection()
    VALID_MODES = [0o777, 0o775, 0o770, 0o755, 0o750, 0o711, 0o710, 0o700,
                   0o666, 0o664, 0o660, 0o644, 0o640, 0o600,
                   0o555, 0o551, 0o550, 0o511, 0o510, 0o500,
                   0o444, 0o440, 0o400]

    INVALID_MODES = [777, 775, 770, 755, 750, 711, 710, 700,
                     666, 664, 660, 644, 640, 622, 620, 600,
                     555, 551, 550,  # 511 == 0o777, 510 == 0o776, 500 == 0o764
                     444, 440, 400]

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
            self.assertFalse(self.rule.is_invalid_permission(mode),
                             msg="0o%o should be a valid mode" % mode)

    def test_invalid_modes(self):
        for mode in self.INVALID_MODES:
            self.assertTrue(self.rule.is_invalid_permission(mode),
                            msg="%d should be an invalid mode" % mode)
