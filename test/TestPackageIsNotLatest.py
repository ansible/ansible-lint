import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.PackageIsNotLatestRule import PackageIsNotLatestRule
from ansiblelint.runner import Runner


class TestPackageIsNotLatestRule(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(PackageIsNotLatestRule())

    def test_package_not_latest_positive(self):
        success = 'test/package-check-success.yml'
        good_runner = Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

    def test_package_not_latest_negative(self):
        failure = 'test/package-check-failure.yml'
        bad_runner = Runner(self.collection, failure, [], [], [])
        errs = bad_runner.run()
        self.assertEqual(3, len(errs))
