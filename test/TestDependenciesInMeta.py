import unittest
import ansible

from ansiblelint import Runner, RulesCollection
from ansiblelint.rules.EnvVarsInCommandRule import EnvVarsInCommandRule
from pkg_resources import parse_version


class TestDependenciesInMeta(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(EnvVarsInCommandRule())

    def bitbucket_in_meta_dependency_is_ok(self):
        success = 'test/dependency-in-meta/bitbucket.yml'
        good_runner = Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

    def galaxy_dependency_is_ok(self):
        success = 'test/dependency-in-meta/galaxy.yml'
        good_runner = Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

    def github_dependency_is_ok(self):
        success = 'test/dependency-in-meta/github.yml'
        good_runner = Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

    def webserver_dependency_is_ok(self):
        success = 'test/dependency-in-meta/webserver.yml'
        good_runner = Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

    def gitlab_dependency_is_ok(self):
        success = 'test/dependency-in-meta/gitlab.yml'
        good_runner = Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())
