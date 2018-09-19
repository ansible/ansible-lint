import os
import unittest

from ansiblelint import Runner, RulesCollection


class TestDependenciesInMeta(unittest.TestCase):

    def setUp(self):
        rulesdir = os.path.join('lib', 'ansiblelint', 'rules')
        self.rules = RulesCollection.create_from_directory(rulesdir)

    def test_bitbucket_in_meta_dependency_is_ok(self):
        filename = 'test/dependency-in-meta/bitbucket.yml'
        self.assertEqual([], Runner(self.rules, filename, [], [], []).run())

    def test_galaxy_dependency_is_ok(self):
        filename = 'test/dependency-in-meta/galaxy.yml'
        good_runner = Runner(self.rules, filename, [], [], [])
        self.assertEqual([], good_runner.run())

    def test_github_dependency_is_ok(self):
        filename = 'test/dependency-in-meta/github.yml'
        good_runner = Runner(self.rules, filename, [], [], [])
        self.assertEqual([], good_runner.run())

    def test_webserver_dependency_is_ok(self):
        filename = 'test/dependency-in-meta/webserver.yml'
        good_runner = Runner(self.rules, filename, [], [], [])
        self.assertEqual([], good_runner.run())

    def test_gitlab_dependency_is_ok(self):
        filename = 'test/dependency-in-meta/gitlab.yml'
        good_runner = Runner(self.rules, filename, [], [], [])
        self.assertEqual([], good_runner.run())
