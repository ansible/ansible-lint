import os
import unittest
import tempfile
import shutil

from ansiblelint import Runner, RulesCollection

PLAY_INCLUDE = '''
- hosts: all
  tasks:
    - include: some_file.yml
'''


class TestIncludeMissingFileRule(unittest.TestCase):
    def setUp(self):
        rulesdir = os.path.join('lib', 'ansiblelint', 'rules')
        self.rules = RulesCollection([rulesdir])

        # make dir and write role tasks to import or include
        self.play_root = tempfile.mkdtemp()
        # role_path = os.path.join(self.play_root, 'test-role', 'tasks')
        # os.makedirs(role_path)
        # with open(os.path.join(role_path, 'main.yml'), 'w') as f_main:
        #     f_main.write(ROLE_TASKS_MAIN)
        # with open(os.path.join(role_path, 'world.yml'), 'w') as f_world:
        #     f_world.write(ROLE_TASKS_WORLD)

    def tearDown(self):
        shutil.rmtree(self.play_root)

    def _get_play_file(self, playbook_text):
        with open(os.path.join(self.play_root, 'playbook.yml'), 'w') as f_play:
            f_play.write(playbook_text)
        return f_play

    def test_include(self):
        fh = self._get_play_file(PLAY_INCLUDE)
        runner = Runner(self.rules, fh.name, [], [], [])
        results = runner.run()
        print(results)
        assert 'referenced missing file in' in str(results)
        assert 'playbook.yml:2' in str(results)
        assert 'some_file.yml' in str(results)
