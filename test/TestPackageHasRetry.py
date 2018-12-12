import unittest

from ansiblelint import RulesCollection
from ansiblelint.rules.PackageHasRetryRule import PackageHasRetryRule
from test import RunFromText

SUCCESS = '''
---
- hosts: hosts
  tasks:
    - name: "Package has retry test success"
      apt:
        pkg: foo
      register: result
      until: result|success

    - name: remove software
      package:
        name: some_package
        state: absent
'''

FAILURE = '''
---
- hosts: hosts
  tasks:
    - name: "Package has retry test failure"
      apt:
        pkg: foo
    - name: "Package has retry test failure"
      macports:
        pkg: foo
'''


class TestPackageHasRetry(unittest.TestCase):
    collection = RulesCollection()
    collection.register(PackageHasRetryRule())

    def setUp(self):
        self.runner = RunFromText(self.collection)

    def test_file_positive(self):
        results = self.runner.run_playbook(SUCCESS)
        self.assertEqual(0, len(results))

    def test_file_negative(self):
        results = self.runner.run_playbook(FAILURE)
        self.assertEqual(2, len(results))
