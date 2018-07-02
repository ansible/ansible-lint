import unittest
import ansible

from ansiblelint import Runner, RulesCollection
from ansiblelint.rules.EnvVarsInCommandRule import EnvVarsInCommandRule
from pkg_resources import parse_version


class TestGitRepoInMeta(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(EnvVarsInCommandRule())

    def test_file_positive(self):
        success = 'test/git-dependency-in-meta/main.yml'
        good_runner = Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())
