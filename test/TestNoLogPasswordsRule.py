import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner
from ansiblelint.rules.NoLogPasswordsRule import NoLogPasswordsRule


class TestNoLogPasswordsRule(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(NoLogPasswordsRule())

    def test_file_positive(self):
        success = 'examples/playbooks/no-log-passwords-success.yml'
        good_runner = Runner(success, rules=self.collection)
        self.assertEqual([], good_runner.run())

    def test_file_negative(self):
        failure = 'examples/playbooks/no-log-passwords-failure.yml'
        bad_runner = Runner(failure, rules=self.collection)
        errs = bad_runner.run()
        self.assertEqual(3, len(errs))
