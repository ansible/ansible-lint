import os
import unittest

from ansiblelint import Runner, RulesCollection


class TestDependenciesInMeta(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        rulesdir = os.path.join('lib', 'ansiblelint', 'rules')
        self.rules = RulesCollection.create_from_directory(rulesdir)

    def bitbucket_in_meta_dependency_is_ok(self):
        filename = 'test/dependency-in-meta/bitbucket.yml'
        self.assertEqual([], Runner(self.rules, filename, [], [], []).run())

    def galaxy_dependency_is_ok(self):
        filename = 'test/dependency-in-meta/galaxy.yml'
        good_runner = Runner(self.rules, filename, [], [], [])
        self.assertEqual([], good_runner.run())

    def github_dependency_is_ok(self):
        filename = 'test/dependency-in-meta/github.yml'
        good_runner = Runner(self.rules, filename, [], [], [])
        self.assertEqual([], good_runner.run())

    def webserver_dependency_is_ok(self):
        filename = 'test/dependency-in-meta/webserver.yml'
        good_runner = Runner(self.rules, filename, [], [], [])
        self.assertEqual([], good_runner.run())

    def gitlab_dependency_is_ok(self):
        filename = 'test/dependency-in-meta/gitlab.yml'
        good_runner = Runner(self.rules, filename, [], [], [])
        self.assertEqual([], good_runner.run())
