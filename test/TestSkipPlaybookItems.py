import unittest
import os

from ansiblelint import RulesCollection
from test import RunFromText


PLAYBOOK_PRE_TASKS = '''
- hosts: all
  tasks:
    - name: bad git 1  # noqa 401
      action: git a=b c=d
    - name: bad git 2
      action: git a=b c=d
  pre_tasks:
    - name: bad git 3  # noqa 401
      action: git a=b c=d
    - name: bad git 4
      action: git a=b c=d
'''

PLAYBOOK_POST_TASKS = '''
- hosts: all
  tasks:
    - name: bad git 1  # noqa 401
      action: git a=b c=d
    - name: bad git 2
      action: git a=b c=d
  post_tasks:
    - name: bad git 3  # noqa 401
      action: git a=b c=d
    - name: bad git 4
      action: git a=b c=d
'''

PLAYBOOK_HANDLERS = '''
- hosts: all
  tasks:
    - name: bad git 1  # noqa 401
      action: git a=b c=d
    - name: bad git 2
      action: git a=b c=d
  handlers:
    - name: bad git 3  # noqa 401
      action: git a=b c=d
    - name: bad git 4
      action: git a=b c=d
'''

PLAYBOOK_TWO_PLAYS = '''
- hosts: all
  tasks:
    - name: bad git 1  # noqa 401
      action: git a=b c=d
    - name: bad git 2
      action: git a=b c=d

- hosts: all
  tasks:
    - name: bad git 3  # noqa 401
      action: git a=b c=d
    - name: bad git 4
      action: git a=b c=d
'''

PLAYBOOK_WITH_BLOCK = '''
- hosts: all
  tasks:
  - name: bad git 1  # noqa 401
    action: git a=b c=d
  - name: bad git 2
    action: git a=b c=d
  - name: Block with rescue and always section
    block:
      - name: bad git 3  # noqa 401
        action: git a=b c=d
      - name: bad git 4
        action: git a=b c=d
    rescue:
      - name: bad git 5  # noqa 401
        action: git a=b c=d
      - name: bad git 6
        action: git a=b c=d
    always:
      - name: bad git 7  # noqa 401
        action: git a=b c=d
      - name: bad git 8
        action: git a=b c=d
'''


class TestSkipPlaybookItems(unittest.TestCase):
    rulesdir = os.path.join('lib', 'ansiblelint', 'rules')
    collection = RulesCollection.create_from_directory(rulesdir)

    def setUp(self):
        self.runner = RunFromText(self.collection)

    def test_pre_tasks(self):
        results = self.runner.run_playbook(PLAYBOOK_PRE_TASKS)
        self.assertEqual(2, len(results))

    def test_post_tasks(self):
        results = self.runner.run_playbook(PLAYBOOK_POST_TASKS)
        self.assertEqual(2, len(results))

    def test_play_handlers(self):
        results = self.runner.run_playbook(PLAYBOOK_HANDLERS)
        self.assertEqual(2, len(results))

    def test_two_plays(self):
        results = self.runner.run_playbook(PLAYBOOK_TWO_PLAYS)
        self.assertEqual(2, len(results))

    def test_with_block(self):
        results = self.runner.run_playbook(PLAYBOOK_WITH_BLOCK)
        self.assertEqual(4, len(results))
