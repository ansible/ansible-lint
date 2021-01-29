# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.PackageIsNotLatestRule import PackageIsNotLatestRule
from ansiblelint.runner import Runner


class TestPackageIsNotLatestRule(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(PackageIsNotLatestRule())

    def test_package_not_latest_positive(self):
        success = 'examples/playbooks/package-check-success.yml'
        good_runner = Runner(
            success,
            rules=self.collection)
        self.assertEqual([], good_runner.run())

    def test_package_not_latest_negative(self):
        failure = 'examples/playbooks/package-check-failure.yml'
        bad_runner = Runner(
            failure,
            rules=self.collection)
        errs = bad_runner.run()
        self.assertEqual(4, len(errs))
