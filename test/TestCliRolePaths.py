# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import os
import unittest
from pathlib import Path
from typing import Dict

import pytest

from ansiblelint.testing import run_ansible_lint
from ansiblelint.text import strip_ansi_escape


class TestCliRolePaths(unittest.TestCase):
    def setUp(self) -> None:
        self.local_test_dir = os.path.realpath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "examples")
        )

    def test_run_single_role_path_no_trailing_slash_module(self) -> None:
        cwd = self.local_test_dir
        role_path = 'roles/test-role'

        result = run_ansible_lint(role_path, cwd=cwd)
        assert 'Use shell only when shell functionality is required' in result.stdout

    def test_run_single_role_path_no_trailing_slash_script(self) -> None:
        cwd = self.local_test_dir
        role_path = 'roles/test-role'

        result = run_ansible_lint(role_path, cwd=cwd, executable="ansible-lint")
        assert 'Use shell only when shell functionality is required' in result.stdout

    def test_run_single_role_path_with_trailing_slash(self) -> None:
        cwd = self.local_test_dir
        role_path = 'roles/test-role/'

        result = run_ansible_lint(role_path, cwd=cwd)
        assert 'Use shell only when shell functionality is required' in result.stdout

    def test_run_multiple_role_path_no_trailing_slash(self) -> None:
        cwd = self.local_test_dir
        role_path = 'roles/test-role'

        result = run_ansible_lint(role_path, cwd=cwd)
        assert 'Use shell only when shell functionality is required' in result.stdout

    def test_run_multiple_role_path_with_trailing_slash(self) -> None:
        cwd = self.local_test_dir
        role_path = 'roles/test-role/'

        result = run_ansible_lint(role_path, cwd=cwd)
        assert 'Use shell only when shell functionality is required' in result.stdout

    def test_run_inside_role_dir(self) -> None:
        cwd = os.path.join(self.local_test_dir, 'roles/test-role/')
        role_path = '.'

        result = run_ansible_lint(role_path, cwd=cwd)
        assert 'Use shell only when shell functionality is required' in result.stdout

    def test_run_role_three_dir_deep(self) -> None:
        cwd = self.local_test_dir
        role_path = 'testproject/roles/test-role'

        result = run_ansible_lint(role_path, cwd=cwd)
        assert 'Use shell only when shell functionality is required' in result.stdout

    def test_run_playbook(self) -> None:
        """Call ansible-lint the way molecule does."""
        cwd = os.path.abspath(os.path.join(self.local_test_dir, 'roles/test-role'))
        lintable = 'molecule/default/include-import-role.yml'
        role_path = str(Path(cwd).parent.resolve())

        env = os.environ.copy()
        env['ANSIBLE_ROLES_PATH'] = role_path

        result = run_ansible_lint(lintable, cwd=cwd, env=env)
        assert 'Use shell only when shell functionality is required' in result.stdout

    def test_run_role_name_invalid(self) -> None:
        cwd = self.local_test_dir
        role_path = 'roles/invalid-name'

        result = run_ansible_lint(role_path, cwd=cwd)
        assert 'role-name: Role name invalid-name does not match' in strip_ansi_escape(
            result.stdout
        )

    def test_run_role_name_with_prefix(self) -> None:
        cwd = self.local_test_dir
        role_path = 'roles/ansible-role-foo'

        result = run_ansible_lint("-v", role_path, cwd=cwd)
        assert len(result.stdout) == 0
        assert (
            "Added ANSIBLE_ROLES_PATH=~/.ansible/roles:/usr/share/ansible/roles:/etc/ansible/roles:roles"
            in result.stderr
        )
        assert result.returncode == 0

    def test_run_role_name_from_meta(self) -> None:
        cwd = self.local_test_dir
        role_path = 'roles/valid-due-to-meta'

        result = run_ansible_lint("-v", role_path, cwd=cwd)
        assert len(result.stdout) == 0
        assert (
            "Added ANSIBLE_ROLES_PATH=~/.ansible/roles:/usr/share/ansible/roles:/etc/ansible/roles:roles"
            in result.stderr
        )
        assert result.returncode == 0

    def test_run_invalid_role_name_from_meta(self) -> None:
        cwd = self.local_test_dir
        role_path = 'roles/invalid_due_to_meta'

        result = run_ansible_lint(role_path, cwd=cwd)
        assert (
            'role-name: Role name invalid-due-to-meta does not match'
            in strip_ansi_escape(result.stdout)
        )

    def test_run_single_role_path_with_roles_path_env(self) -> None:
        """Test for role name collision with ANSIBLE_ROLES_PATH.

        Test if ansible-lint chooses the role in the current directory when the role
        specified as parameter exists in the current directory and the ANSIBLE_ROLES_PATH.
        """
        cwd = self.local_test_dir
        role_path = 'roles/test-role'

        env = os.environ.copy()
        env['ANSIBLE_ROLES_PATH'] = os.path.realpath(
            os.path.join(cwd, "../examples/roles")
        )

        result = run_ansible_lint(role_path, cwd=cwd, env=env)
        assert 'Use shell only when shell functionality is required' in result.stdout


@pytest.mark.parametrize(
    ('result', 'env'),
    ((True, {"GITHUB_ACTIONS": "true", "GITHUB_WORKFLOW": "foo"}), (False, None)),
    ids=("on", "off"),
)
def test_run_playbook_github(result: bool, env: Dict[str, str]) -> None:
    """Call ansible-lint simulating GitHub Actions environment."""
    cwd = str(Path(__file__).parent.parent.resolve())
    role_path = 'examples/playbooks/example.yml'

    if env is None:
        env = {}
    env['PATH'] = os.environ['PATH']
    result_gh = run_ansible_lint(role_path, cwd=cwd, env=env)

    expected = (
        '::warning file=examples/playbooks/example.yml,line=44,severity=VERY_LOW::package-latest '
        'Package installs should not use latest'
    )
    assert (expected in result_gh.stdout) is result
