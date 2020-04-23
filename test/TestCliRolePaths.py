import os
import subprocess

import pytest

local_test_dir = os.path.dirname(os.path.realpath(__file__))


def run_ansible_lint(cwd, bin, role_path, env=None):
    command = '{} {}'.format(bin, role_path)

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


@pytest.mark.parametrize(('cwd', 'binary', 'role_path', 'env'), (
    pytest.param(local_test_dir,
                 '../bin/ansible-lint',
                 'test-role',
                 None,
                 id='single_role_path_no_trailing_slash'),
    pytest.param(local_test_dir,
                 '../bin/ansible-lint',
                 'test-role/',
                 None,
                 id='single_roles_path_with_trailing_slash'),
    pytest.param(local_test_dir,
                 '../bin/ansible-lint',
                 'roles/test-role',
                 None,
                 id='multiple_role_path_no_trailing_slash'),
    pytest.param(local_test_dir,
                 '../bin/ansible-lint',
                 'roles/test-role/',
                 None,
                 id='multiple_role_path_with_trailing_slash'),
    pytest.param(os.path.join(local_test_dir, 'test-role/'),
                 '../../bin/ansible-lint',
                 '.',
                 None,
                 id='inside_a_role'),
    pytest.param(local_test_dir,
                 '../bin/ansible-lint',
                 'testproject/roles/test-role',
                 None,
                 id='three_dirs_deep'),
    pytest.param(os.path.normpath(os.path.join(local_test_dir, 'roles/test-role')),
                 os.path.normpath(os.path.join(local_test_dir, '../bin/ansible-lint')),
                 'molecule/default/include-import-role.yml',
                 {'ANSIBLE_ROLES_PATH': os.path.join(local_test_dir, 'roles')},
                 # marks=pytest.mark.xfail,  # Cannot figure out why yet...
                 id='playbook'),
))
def test_main_subprocess(cwd, binary, role_path, env):
    if env:
        _env = os.environ.copy()
        _env.update(env)
        env = _env
    result = run_ansible_lint(cwd=cwd, bin=binary, role_path=role_path, env=env)

    assert 'Use shell only when shell functionality is required' in str(result)


def test_run_playbook():
    """Call ansible-lint the way molecule does."""
    top_src_dir = os.path.dirname(local_test_dir)
    cwd = os.path.join(top_src_dir, 'test/roles/test-role')
    bin = top_src_dir + '/bin/ansible-lint'
    role_path = 'molecule/default/include-import-role.yml'

    env = os.environ.copy()
    env['ANSIBLE_ROLES_PATH'] = os.path.dirname(cwd)

    result = run_ansible_lint(cwd=cwd, bin=bin, role_path=role_path, env=env)

    assert 'Use shell only when shell functionality is required' in str(result)
