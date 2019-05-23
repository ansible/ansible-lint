import os
import unittest
import tempfile
import shutil

from ansiblelint import Runner, RulesCollection

IMPORTED_PLAYBOOK = '''
- hosts: all
  tasks:
    - name: success
      fail: msg="fail"
      when: False
'''

MAIN_PLAYBOOK = '''
- hosts: all

  tasks:
    - name: should be shell  # noqa 305 301
      shell: echo lol

- import_playbook: imported_playbook.yml
'''


class TestSkipBeforeImport(unittest.TestCase):
    def setUp(self):
        rulesdir = os.path.join('lib', 'ansiblelint', 'rules')
        self.rules = RulesCollection.create_from_directory(rulesdir)

        # make dir and write role tasks to import or include
        self.play_root = tempfile.mkdtemp()
        with open(os.path.join(self.play_root, 'imported_playbook.yml'), 'w') as f_main:
            f_main.write(IMPORTED_PLAYBOOK)

    def tearDown(self):
        shutil.rmtree(self.play_root)

    def _get_play_file(self, playbook_text):
        with open(os.path.join(self.play_root, 'playbook.yml'), 'w') as f_play:
            f_play.write(playbook_text)
        return f_play

    def test_skip_import_playbook(self):
        fh = self._get_play_file(MAIN_PLAYBOOK)
        runner = Runner(self.rules, fh.name, [], [], [])
        results = runner.run()
        self.assertEqual(0, len(results))
