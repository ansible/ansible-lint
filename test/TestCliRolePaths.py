# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import os
import unittest
from pathlib import Path

import pytest

from ansiblelint.testing import run_ansible_lint


class TestCliRolePaths(unittest.TestCase):
    def setUp(self):
        self.local_test_dir = os.path.dirname(os.path.realpath(__file__))

    def test_run_single_role_path_no_trailing_slash_module(self):
        cwd = self.local_test_dir
        role_path = 'test-role'

        result = run_ansible_lint(role_path, cwd=cwd)
        self.assertIn('Use shell only when shell functionality is required',
                      result.stdout)

    def test_run_single_role_path_no_trailing_slash_script(self):
        cwd = self.local_test_dir
        role_path = 'test-role'

        result = run_ansible_lint(role_path, cwd=cwd, bin="ansible-lint")
        self.assertIn('Use shell only when shell functionality is required',
                      result.stdout)

    def test_run_single_role_path_with_trailing_slash(self):
        cwd = self.local_test_dir
        role_path = 'test-role/'

        result = run_ansible_lint(role_path, cwd=cwd)
        self.assertIn('Use shell only when shell functionality is required',
                      result.stdout)

    def test_run_multiple_role_path_no_trailing_slash(self):
        cwd = self.local_test_dir
        role_path = 'roles/test-role'

        result = run_ansible_lint(role_path, cwd=cwd)
        self.assertIn('Use shell only when shell functionality is required',
                      result.stdout)

    def test_run_multiple_role_path_with_trailing_slash(self):
        cwd = self.local_test_dir
        role_path = 'roles/test-role/'

        result = run_ansible_lint(role_path, cwd=cwd)
        self.assertIn('Use shell only when shell functionality is required',
                      result.stdout)

    def test_run_inside_role_dir(self):
        cwd = os.path.join(self.local_test_dir, 'test-role/')
        role_path = '.'

        result = run_ansible_lint(role_path, cwd=cwd)
        self.assertIn('Use shell only when shell functionality is required',
                      result.stdout)

    def test_run_role_three_dir_deep(self):
        cwd = self.local_test_dir
        role_path = 'testproject/roles/test-role'

        result = run_ansible_lint(role_path, cwd=cwd)
        self.assertIn('Use shell only when shell functionality is required',
                      result.stdout)

    def test_run_playbook(self):
        """Call ansible-lint the way molecule does."""
        top_src_dir = os.path.dirname(self.local_test_dir)
        cwd = os.path.join(top_src_dir, 'test/roles/test-role')
        role_path = 'molecule/default/include-import-role.yml'

        env = os.environ.copy()
        env['ANSIBLE_ROLES_PATH'] = os.path.dirname(cwd)

        result = run_ansible_lint(role_path, cwd=cwd, env=env)
        self.assertIn('Use shell only when shell functionality is required', result.stdout)

    def test_run_role_name_invalid(self):
        cwd = self.local_test_dir
        role_path = 'roles/invalid-name'

        result = run_ansible_lint(role_path, cwd=cwd)
        assert '106: Role name invalid-name does not match' in result.stdout

    def test_run_role_name_with_prefix(self):
        cwd = self.local_test_dir
        role_path = 'roles/ansible-role-foo'

        result = run_ansible_lint(role_path, cwd=cwd)
        assert len(result.stdout) == 0
        assert len(result.stderr) == 0
        assert result.returncode == 0

    def test_run_role_name_from_meta(self):
        cwd = self.local_test_dir
        role_path = 'roles/valid-due-to-meta'

        result = run_ansible_lint(role_path, cwd=cwd)
        assert len(result.stdout) == 0
        assert len(result.stderr) == 0
        assert result.returncode == 0

    def test_run_invalid_role_name_from_meta(self):
        cwd = self.local_test_dir
        role_path = 'roles/invalid_due_to_meta'

        result = run_ansible_lint(role_path, cwd=cwd)
        assert '106: Role name invalid-due-to-meta does not match' in result.stdout

    def test_run_single_role_path_with_roles_path_env(self):
        """Test for role name collision with ANSIBLE_ROLES_PATH.

        Test if ansible-lint chooses the role in the current directory when the role
        specified as parameter exists in the current directory and the ANSIBLE_ROLES_PATH.
        """
        cwd = self.local_test_dir
        role_path = 'test-role'

        env = os.environ.copy()
        env['ANSIBLE_ROLES_PATH'] = os.path.join(cwd, 'use-as-default-roles-path')

        result = run_ansible_lint(role_path, cwd=cwd, env=env)
        assert 'Use shell only when shell functionality is required' in result.stdout


@pytest.mark.parametrize(('result', 'env'), (
    (True, {
        "GITHUB_ACTIONS": "true",
        "GITHUB_WORKFLOW": "foo"
    }),
    (False, None)),
    ids=("on", "off"))
def test_run_playbook_github(result, env):
    """Call ansible-lint simulating GitHub Actions environment."""
    cwd = str(Path(__file__).parent.parent.resolve())
    role_path = 'examples/example.yml'

    if env is None:
        env = {}
    env['PATH'] = os.environ['PATH']
    result_gh = run_ansible_lint(role_path, cwd=cwd, env=env)

    expected = (
        '::warning file=examples/example.yml,line=44,severity=VERY_LOW::E403 '
        'Package installs should not use latest'
    )
    assert (expected in result_gh.stdout) is result
