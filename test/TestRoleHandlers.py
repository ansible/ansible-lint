import unittest
from ansiblelint import Runner, RulesCollection
from ansiblelint.rules.UseHandlerRatherThanWhenChangedRule import UseHandlerRatherThanWhenChangedRule

class TestRoleHandlers(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(UseHandlerRatherThanWhenChangedRule())

    def test_role_handler_positive(self):
        success = 'test/role-with-handler/main.yml'
        good_runner = Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())
