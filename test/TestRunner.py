import os
import unittest

import ansiblelint
from ansiblelint import RulesCollection


class TestRule(unittest.TestCase):

    def setUp(self):
        rulesdir = os.path.join('lib', 'ansiblelint', 'rules')
        self.rules = RulesCollection.create_from_directory(rulesdir)

    def test_runner_count(self):
        filename = 'test/nomatchestest.txt'
        runner = ansiblelint.Runner(self.rules, {filename}, [], [])
        assert (len(runner.run()) == 0)
