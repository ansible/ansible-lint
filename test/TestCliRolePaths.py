import unittest
import subprocess
import os


class TestCliRolePaths(unittest.TestCase):
    def setUp(self):
        self.local_test_dir = os.path.dirname(os.path.realpath(__file__))

    def run_ansible_lint(self, cwd, bin, role_path):
        command = '{} {}'.format(bin, role_path)

        result, err = subprocess.Popen(
            [command],
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        ).communicate()

        self.assertFalse(err, 'Expected no error but was ' + str(err))

        return result

    def test_run_single_role_path_no_trailing_slash(self):
        cwd = self.local_test_dir
        bin = '../bin/ansible-lint'
        role_path = 'test-role'

        result = self.run_ansible_lint(cwd=cwd, bin=bin, role_path=role_path)
        self.assertIn('Use shell only when shell functionality is required',
                      str(result))

    def test_run_single_role_path_with_trailing_slash(self):
        cwd = self.local_test_dir
        bin = '../bin/ansible-lint'
        role_path = 'test-role/'

        result = self.run_ansible_lint(cwd=cwd, bin=bin, role_path=role_path)
        self.assertIn('Use shell only when shell functionality is required',
                      str(result))

    def test_run_multiple_role_path_no_trailing_slash(self):
        cwd = self.local_test_dir
        bin = '../bin/ansible-lint'
        role_path = 'roles/test-role'

        result = self.run_ansible_lint(cwd=cwd, bin=bin, role_path=role_path)
        self.assertIn('Use shell only when shell functionality is required',
                      str(result))

    def test_run_multiple_role_path_with_trailing_slash(self):
        cwd = self.local_test_dir
        bin = '../bin/ansible-lint'
        role_path = 'roles/test-role/'

        result = self.run_ansible_lint(cwd=cwd, bin=bin, role_path=role_path)
        self.assertIn('Use shell only when shell functionality is required',
                      str(result))

    def test_run_inside_role_dir(self):
        cwd = os.path.join(self.local_test_dir, 'test-role/')
        bin = '../../bin/ansible-lint'
        role_path = '.'

        result = self.run_ansible_lint(cwd=cwd, bin=bin, role_path=role_path)
        self.assertIn('Use shell only when shell functionality is required',
                      str(result))

    def test_run_role_three_dir_deep(self):
        cwd = self.local_test_dir
        bin = '../bin/ansible-lint'
        role_path = 'roles/roles/test-role'

        result = self.run_ansible_lint(cwd=cwd, bin=bin, role_path=role_path)
        self.assertIn('Use shell only when shell functionality is required',
                      str(result))
