import unittest
import ansible

from ansiblelint import Runner, RulesCollection
from ansiblelint.rules.EnvVarsInCommandRule import EnvVarsInCommandRule
from pkg_resources import parse_version


class TestGitRepoInMeta(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(EnvVarsInCommandRule())

    def git_in_meta_dependency_is_ok(self):
        success = 'test/dependency-in-meta/git.yml'
        good_runner = Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())
