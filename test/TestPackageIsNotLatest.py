import unittest
import ansiblelint.utils
from ansiblelint import RulesCollection
from ansiblelint.rules.PackageIsNotLatestRule import PackageIsNotLatestRule


class TestPackageIsNotLatestRule(unittest.TestCase):
    collection = RulesCollection()

    def test_package_not_latest_positive(self):
        self.collection.register(PackageIsNotLatestRule())
        success = 'test/package-check-success.yml'
        good_runner = ansiblelint.Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

    def test_package_not_latest_negative(self):
        self.collection.register(PackageIsNotLatestRule())
        failure = 'test/package-check-failure.yml'
        bad_runner = ansiblelint.Runner(self.collection, failure, [], [], [])
        errs = bad_runner.run()
        self.assertEqual(3, len(errs))
