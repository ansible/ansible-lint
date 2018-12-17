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
      until: result is succeeded

    - name: remove software
      package:
        name: some_package
        state: absent

    - name: Install from file - remote
      apt:
        deb: https://example.com/python-ppq_0.1-1_all.deb
        state: present
      until: result.rc == 0

    - name: Install a .deb package
      apt:
        deb: /tmp/mypackage.deb

    - name: install software from a local source
      package:
        name: "/tmp/some_package.rpm"
        state: present

    - name: packaging key
      apt_key:
        data: "{{ lookup('file', release_key) }}"
        id: "{{ release_key_id }}"
        state: present
'''

FAILURE = '''
---
- hosts: hosts
  tasks:
    - name: "Package has retry test failure"
      apt:
        package: foo
    - name: "Package has retry test failure"
      macports:
        pkg: foo
    - name: Install from file - remote
      apt:
        deb: https://example.com/python-ppq_0.1-1_all.deb
        state: present
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
        self.assertEqual(3, len(results))
