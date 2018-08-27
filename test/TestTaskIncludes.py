import os
import unittest
import ansible

from ansiblelint import Runner, RulesCollection
from pkg_resources import parse_version


class TestTaskIncludes(unittest.TestCase):

    def setUp(self):
        rulesdir = os.path.join('lib', 'ansiblelint', 'rules')
        self.rules = RulesCollection.create_from_directory(rulesdir)

    def test_block_included_tasks(self):
        filename = 'test/blockincludes.yml'
        runner = Runner(self.rules, filename, [], [], [])
        runner.run()
        self.assertEqual(len(runner.playbooks), 4)

    def test_block_included_tasks_with_rescue_and_always(self):
        filename = 'test/blockincludes2.yml'
        runner = Runner(self.rules, filename, [], [], [])
        runner.run()
        self.assertEqual(len(runner.playbooks), 4)

    def test_included_tasks(self):
        filename = 'test/taskincludes.yml'
        runner = Runner(self.rules, filename, [], [], [])
        runner.run()
        self.assertEqual(len(runner.playbooks), 4)

    @unittest.skipIf(parse_version(ansible.__version__) < parse_version('2.4'), "not supported with ansible < 2.4")
    def test_include_tasks_2_4_style(self):
        filename = 'test/taskincludes_2_4_style.yml'
        runner = Runner(self.rules, filename, [], [], [])
        runner.run()
        self.assertEqual(len(runner.playbooks), 4)

    @unittest.skipIf(parse_version(ansible.__version__) < parse_version('2.4'), "not supported with ansible < 2.4")
    def test_import_tasks_2_4_style(self):
        filename = 'test/taskimports.yml'
        runner = Runner(self.rules, filename, [], [], [])
        runner.run()
        self.assertEqual(len(runner.playbooks), 4)

    def test_include_tasks_with_block_include(self):
        filename = 'test/include-in-block.yml'
        runner = Runner(self.rules, filename, [], [], [])
        runner.run()
        self.assertEqual(len(runner.playbooks), 3)

    @unittest.skipIf(parse_version(ansible.__version__) < parse_version('2.4'), "not supported with ansible < 2.4")
    def test_include_tasks_in_role(self):
        filename = 'test/include-import-tasks-in-role.yml'
        runner = Runner(self.rules, filename, [], [], [])
        runner.run()
        self.assertEqual(len(runner.playbooks), 4)
