import unittest
from ansiblelint import Runner, RulesCollection
from ansiblelint.rules.PackageIsNotLatestRule import PackageIsNotLatestRule

from importlib_metadata import version as get_dist_version
from packaging.version import Version
import pytest


class TestPackageIsNotLatestRule(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(PackageIsNotLatestRule())

    @pytest.mark.xfail(
        Version(get_dist_version('ansible')) >= Version('2.10.dev0') and
        Version(get_dist_version('ansible-base')) >= Version('2.10.dev0'),
        reason='Post-split Ansible Core Engine does not have '
        'the module used in the test playbook.'
        ' Ref: https://github.com/ansible/ansible-lint/issues/703.'
        ' Ref: https://github.com/ansible/ansible/pull/68598.',
        raises=SystemExit,
        strict=True,
    )
    def test_package_not_latest_positive(self):
        success = 'test/package-check-success.yml'
        good_runner = Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

    def test_package_not_latest_negative(self):
        failure = 'test/package-check-failure.yml'
        bad_runner = Runner(self.collection, failure, [], [], [])
        errs = bad_runner.run()
        self.assertEqual(3, len(errs))
