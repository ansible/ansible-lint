import os
import unittest
from pathlib import Path

import pytest

from . import run_ansible_lint


class TestCliRolePaths(unittest.TestCase):
    def setUp(self):
        self.local_test_dir = os.path.dirname(os.path.realpath(__file__))

    def test_run_single_role_path_no_trailing_slash_module(self):
        cwd = self.local_test_dir
        role_path = 'test-role'

        result = run_ansible_lint(cwd=cwd, role_path=role_path)
        self.assertIn('Use shell only when shell functionality is required',
                      str(result))

    def test_run_single_role_path_no_trailing_slash_script(self):
        cwd = self.local_test_dir
        role_path = 'test-role'

        result = run_ansible_lint(cwd=cwd, role_path=role_path, bin="ansible-lint")
        self.assertIn('Use shell only when shell functionality is required',
                      str(result))

    def test_run_single_role_path_with_trailing_slash(self):
        cwd = self.local_test_dir
        role_path = 'test-role/'

        result = run_ansible_lint(cwd=cwd, role_path=role_path)
        self.assertIn('Use shell only when shell functionality is required',
                      str(result))

    def test_run_multiple_role_path_no_trailing_slash(self):
        cwd = self.local_test_dir
        role_path = 'roles/test-role'

        result = run_ansible_lint(cwd=cwd, role_path=role_path)
        self.assertIn('Use shell only when shell functionality is required',
                      str(result))

    def test_run_multiple_role_path_with_trailing_slash(self):
        cwd = self.local_test_dir
        role_path = 'roles/test-role/'

        result = run_ansible_lint(cwd=cwd, role_path=role_path)
        self.assertIn('Use shell only when shell functionality is required',
                      str(result))

    def test_run_inside_role_dir(self):
        cwd = os.path.join(self.local_test_dir, 'test-role/')
        role_path = '.'

        result = run_ansible_lint(cwd=cwd, role_path=role_path)
        self.assertIn('Use shell only when shell functionality is required',
                      str(result))

    def test_run_role_three_dir_deep(self):
        cwd = self.local_test_dir
        role_path = 'testproject/roles/test-role'

        result = run_ansible_lint(cwd=cwd, role_path=role_path)
        self.assertIn('Use shell only when shell functionality is required',
                      str(result))

    def test_run_playbook(self):
        """Call ansible-lint the way molecule does."""
        top_src_dir = os.path.dirname(self.local_test_dir)
        cwd = os.path.join(top_src_dir, 'test/roles/test-role')
        role_path = 'molecule/default/include-import-role.yml'

        env = os.environ.copy()
        env['ANSIBLE_ROLES_PATH'] = os.path.dirname(cwd)

        result = run_ansible_lint(cwd=cwd, role_path=role_path, env=env)
        self.assertIn('Use shell only when shell functionality is required', str(result))

    def test_run_role_name_invalid(self):
        cwd = self.local_test_dir
        role_path = 'roles/invalid-name'

        result = run_ansible_lint(cwd=cwd, role_path=role_path)
        assert '106 Role name invalid-name does not match' in str(result)


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

    result_gh = run_ansible_lint(cwd=cwd, role_path=role_path, env=env)

    expected = (
        '::error file=examples/example.yml,line=47::[E101] '
        'Deprecated always_run'
    )
    assert (expected in str(result_gh)) is result
