import unittest
from ansiblelint import Runner, RulesCollection

class TestRoleHandlers(unittest.TestCase):
    collection = RulesCollection()

    def test_role_handler_positive(self):
        success = 'test/252/main.yml'
        good_runner = Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

