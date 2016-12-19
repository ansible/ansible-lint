import os
import unittest
import sys

import ansiblelint
from ansiblelint import RulesCollection


class TestTaskIncludes(unittest.TestCase):
    def setUp(self):
        rulesdir = os.path.join('lib', 'ansiblelint', 'rules')
        self.rules = RulesCollection.create_from_directory(rulesdir)

    @unittest.skipIf(sys.version_info > (3, 0), reason="ansible bug")
    def test_included_tasks(self):
        filename = 'test/taskincludes.yml'
        runner = ansiblelint.Runner(self.rules, {filename}, [], [], [])
        runner.run()
        self.assertEqual(len(runner.playbooks), 4)
