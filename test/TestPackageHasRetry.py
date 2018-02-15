import unittest
from ansiblelint import Runner, RulesCollection
from ansiblelint.rules.PackageHasRetryRule import PackageHasRetryRule


class TestPackageHasRetry(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(PackageHasRetryRule())

    def test_file_positive(self):
        success = 'test/packagehasretry-success.yml'
        good_runner = Runner(self.collection, success, [], [], [])
        self.assertEqual(0, len(good_runner.run()))

    def test_file_negative(self):
        failure = 'test/packagehasretry-failure.yml'
        bad_runner = Runner(self.collection, failure, [], [], [])
        self.assertEqual(2, len(bad_runner.run()))
