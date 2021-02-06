# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.UseHandlerRatherThanWhenChangedRule import (
    UseHandlerRatherThanWhenChangedRule,
)
from ansiblelint.runner import Runner


class TestRoleHandlers(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(UseHandlerRatherThanWhenChangedRule())

    def test_role_handler_positive(self):
        success = 'examples/playbooks/role-with-handler.yml'
        good_runner = Runner(success, rules=self.collection)
        self.assertEqual([], good_runner.run())
