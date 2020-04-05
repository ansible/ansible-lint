import os
import unittest
import tempfile
import shutil

from ansiblelint import Runner, RulesCollection

IMPORT_TASKS_MAIN = '''
- oops this is invalid
'''

PLAY_IMPORT_TASKS = '''
- hosts: all

  tasks:
    - import_tasks: import-tasks-main.yml
'''


class TestImportIncludeRole(unittest.TestCase):
    def setUp(self):
        rulesdir = os.path.join('lib', 'ansiblelint', 'rules')
        self.rules = RulesCollection([rulesdir])

        # make dir and write role tasks to import or include
        self.play_root = tempfile.mkdtemp()
        with open(os.path.join(self.play_root, 'import-tasks-main.yml'), 'w') as f_main:
            f_main.write(IMPORT_TASKS_MAIN)

    def tearDown(self):
        shutil.rmtree(self.play_root)

    def _get_play_file(self, playbook_text):
        with open(os.path.join(self.play_root, 'playbook.yml'), 'w') as f_play:
            f_play.write(playbook_text)
        return f_play

    def test_import_tasks_with_malformed_import(self):
        fh = self._get_play_file(PLAY_IMPORT_TASKS)
        runner = Runner(self.rules, fh.name, [], [], [])
        results = runner.run()
        assert 'only when shell functionality is required' in str(results)
