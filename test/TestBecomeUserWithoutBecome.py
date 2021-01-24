# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.BecomeUserWithoutBecomeRule import BecomeUserWithoutBecomeRule
from ansiblelint.runner import Runner


class TestBecomeUserWithoutBecome(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(BecomeUserWithoutBecomeRule())

    def test_file_positive(self):
        success = 'examples/playbooks/become-user-without-become-success.yml'
        good_runner = Runner(
            success,
            rules=self.collection)
        self.assertEqual([], good_runner.run())

    def test_file_negative(self):
        failure = 'examples/playbooks/become-user-without-become-failure.yml'
        bad_runner = Runner(
            failure,
            rules=self.collection)
        errs = bad_runner.run()
        self.assertEqual(3, len(errs))
