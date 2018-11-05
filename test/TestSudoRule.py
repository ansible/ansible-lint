import unittest

from ansiblelint import Runner, RulesCollection
from ansiblelint.rules.SudoRule import SudoRule


class TestSudoRule(unittest.TestCase):
    collection = RulesCollection()
    collection.register(SudoRule())

    def test_file(self):
        file = 'test/sudo.yml'
        runner = Runner(self.collection, file, [], [], [])
        results = runner.run()
        self.assertEqual(4, len(results))

    def test_role(self):
        role_path = 'test/role-sudo'
        runner = Runner(self.collection, role_path, [], [], [])
        results = runner.run()
        self.assertEqual(2, len(results))
