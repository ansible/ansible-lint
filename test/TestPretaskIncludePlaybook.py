import os
import unittest

from ansiblelint import Runner, RulesCollection


class TestTaskIncludes(unittest.TestCase):

    def setUp(self):
        rulesdir = os.path.join('lib', 'ansiblelint', 'rules')
        self.rules = RulesCollection([rulesdir])

    def test_pre_task_include_playbook(self):
        filename = 'test/playbook-include/playbook_pre.yml'
        runner = Runner(self.rules, filename, [], [], [])
        results = runner.run()

        self.assertEqual(len(runner.playbooks), 2)
        self.assertEqual(len(results), 3)
        self.assertIn('Commands should not change things', str(results))

        self.assertNotIn('502', str(results))
        self.assertNotIn('All tasks should be named', str(results))

    def test_post_task_include_playbook(self):
        filename = 'test/playbook-include/playbook_post.yml'
        runner = Runner(self.rules, filename, [], [], [])
        results = runner.run()

        self.assertEqual(len(runner.playbooks), 2)
        self.assertEqual(len(results), 3)
        self.assertIn('Commands should not change things', str(results))

        self.assertNotIn('502', str(results))
        self.assertNotIn('All tasks should be named', str(results))
