import unittest
import subprocess
import os
import sys


class TestCliRolePaths(unittest.TestCase):
    def setUp(self):
        self.local_test_dir = os.path.dirname(os.path.realpath(__file__))

    def run_ansible_lint(self, cwd, role_path=None, bin=None, env=None):
        command = '{} -v {}'.format(
            bin or (sys.executable + " -m ansiblelint"),
            role_path or "")

        result, err = subprocess.Popen(
            [command],
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            env=env,
        ).communicate()

        return result

    def test_run_single_role_path_no_trailing_slash_module(self):
        cwd = self.local_test_dir
        role_path = 'test-role'

        result = self.run_ansible_lint(cwd=cwd, role_path=role_path)
        self.assertIn('Use shell only when shell functionality is required',
                      str(result))

    def test_run_single_role_path_no_trailing_slash_script(self):
        cwd = self.local_test_dir
        role_path = 'test-role'

        result = self.run_ansible_lint(cwd=cwd, role_path=role_path, bin="ansible-lint")
        self.assertIn('Use shell only when shell functionality is required',
                      str(result))

    def test_run_single_role_path_with_trailing_slash(self):
        cwd = self.local_test_dir
        role_path = 'test-role/'

        result = self.run_ansible_lint(cwd=cwd, role_path=role_path)
        self.assertIn('Use shell only when shell functionality is required',
                      str(result))

    def test_run_multiple_role_path_no_trailing_slash(self):
        cwd = self.local_test_dir
        role_path = 'roles/test-role'

        result = self.run_ansible_lint(cwd=cwd, role_path=role_path)
        self.assertIn('Use shell only when shell functionality is required',
                      str(result))

    def test_run_multiple_role_path_with_trailing_slash(self):
        cwd = self.local_test_dir
        role_path = 'roles/test-role/'

        result = self.run_ansible_lint(cwd=cwd, role_path=role_path)
        self.assertIn('Use shell only when shell functionality is required',
                      str(result))

    def test_run_inside_role_dir(self):
        cwd = os.path.join(self.local_test_dir, 'test-role/')
        role_path = '.'

        result = self.run_ansible_lint(cwd=cwd, role_path=role_path)
        self.assertIn('Use shell only when shell functionality is required',
                      str(result))

    def test_run_role_three_dir_deep(self):
        cwd = self.local_test_dir
        role_path = 'testproject/roles/test-role'

        result = self.run_ansible_lint(cwd=cwd, role_path=role_path)
        self.assertIn('Use shell only when shell functionality is required',
                      str(result))

    def test_run_playbook(self):
        """Call ansible-lint the way molecule does."""
        top_src_dir = os.path.dirname(self.local_test_dir)
        cwd = os.path.join(top_src_dir, 'test/roles/test-role')
        role_path = 'molecule/default/include-import-role.yml'

        env = os.environ.copy()
        env['ANSIBLE_ROLES_PATH'] = os.path.dirname(cwd)

        result = self.run_ansible_lint(cwd=cwd, role_path=role_path, env=env)
        self.assertIn('Use shell only when shell functionality is required', str(result))
