import os
import unittest
import tempfile
import shutil

from ansiblelint import Runner, RulesCollection

ROLE_TASKS_MAIN = '''
- name: shell instead of command
  shell: echo hello world
'''

ROLE_TASKS_WORLD = '''
- command: echo this is a task without a name
'''

PLAY_IMPORT_ROLE = '''
- hosts: all

  tasks:
    - import_role:
        name: test-role
'''

PLAY_IMPORT_ROLE_INLINE = '''
- hosts: all

  tasks:
    - import_role: name=test-role
'''

PLAY_INCLUDE_ROLE = '''
- hosts: all

  tasks:
    - include_role:
        name: test-role
        tasks_from: world
'''

PLAY_INCLUDE_ROLE_INLINE = '''
- hosts: all

  tasks:
    - include_role: name=test-role tasks_from=world
'''


class TestImportIncludeRole(unittest.TestCase):
    def setUp(self):
        rulesdir = os.path.join('lib', 'ansiblelint', 'rules')
        self.rules = RulesCollection.create_from_directory(rulesdir)

        # make dir and write role tasks to import or include
        self.play_root = tempfile.mkdtemp()
        role_path = os.path.join(self.play_root, 'test-role', 'tasks')
        os.makedirs(role_path)
        with open(os.path.join(role_path, 'main.yml'), 'w') as f_main:
            f_main.write(ROLE_TASKS_MAIN)
        with open(os.path.join(role_path, 'world.yml'), 'w') as f_world:
            f_world.write(ROLE_TASKS_WORLD)

    def tearDown(self):
        shutil.rmtree(self.play_root)

    def _get_play_file(self, playbook_text):
        with open(os.path.join(self.play_root, 'playbook.yml'), 'w') as f_play:
            f_play.write(playbook_text)
        return f_play

    def test_import_role(self):
        fh = self._get_play_file(PLAY_IMPORT_ROLE)
        runner = Runner(self.rules, fh.name, [], [], [])
        results = runner.run()
        assert 'only when shell functionality is required' in str(results)

    def test_import_role_inline_args(self):
        fh = self._get_play_file(PLAY_IMPORT_ROLE_INLINE)
        runner = Runner(self.rules, fh.name, [], [], [])
        results = runner.run()
        assert 'only when shell functionality is required' in str(results)

    def test_include_role(self):
        fh = self._get_play_file(PLAY_INCLUDE_ROLE)
        runner = Runner(self.rules, fh.name, [], [], [])
        results = runner.run()
        assert 'only when shell functionality is required' in str(results)
        assert 'All tasks should be named' in str(results)

    def test_include_role_inline_args(self):
        fh = self._get_play_file(PLAY_INCLUDE_ROLE_INLINE)
        runner = Runner(self.rules, fh.name, [], [], [])
        results = runner.run()
        assert 'only when shell functionality is required' in str(results)
        assert 'All tasks should be named' in str(results)
