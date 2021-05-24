# Copyright (c) 2020 Sorin Sbarnea <sorin.sbarnea@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""MissingFilePermissionsRule used with ansible-lint."""
import sys
from typing import TYPE_CHECKING, Any, Dict, Set, Union

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.testing import RunFromText

if TYPE_CHECKING:
    from typing import Optional

    from ansiblelint.file_utils import Lintable


# Despite documentation mentioning 'preserve' only these modules support it:
_modules_with_preserve = (
    'copy',
    'template',
)

_MODULES: Set[str] = {
    'archive',
    'community.general.archive',
    'assemble',
    'ansible.builtin.assemble',
    'copy',  # supports preserve
    'ansible.builtin.copy',
    'file',
    'ansible.builtin.file',
    'replace',  # implicit preserve behavior but mode: preserve is invalid
    'ansible.builtin.replace',
    'template',  # supports preserve
    'ansible.builtin.template',
    # 'unarchive',  # disabled because .tar.gz files can have permissions inside
}

_MODULES_WITH_CREATE: Dict[str, bool] = {
    'blockinfile': False,
    'ansible.builtin.blockinfile': False,
    'htpasswd': True,
    'community.general.htpasswd': True,
    'ini_file': True,
    'community.general.ini_file': True,
    'lineinfile': False,
    'ansible.builtin.lineinfile': False,
}


class MissingFilePermissionsRule(AnsibleLintRule):
    id = "risky-file-permissions"
    shortdesc = 'File permissions unset or incorrect'
    description = (
        "Missing or unsupported mode parameter can cause unexpected file "
        "permissions based "
        "on version of Ansible being used. Be explicit, like ``mode: 0644`` to "
        "avoid hitting this rule. Special ``preserve`` value is accepted "
        f"only by {', '.join(_modules_with_preserve)} modules. "
        "See https://github.com/ansible/ansible/issues/71200"
    )
    severity = 'VERY_HIGH'
    tags = ['unpredictability', 'experimental']
    version_added = 'v4.3.0'

    _modules = _MODULES
    _modules_with_create = _MODULES_WITH_CREATE

    def matchtask(
        self, task: Dict[str, Any], file: 'Optional[Lintable]' = None
    ) -> Union[bool, str]:
        module = task["action"]["__ansible_module__"]
        mode = task['action'].get('mode', None)

        if module not in self._modules and module not in self._modules_with_create:
            return False

        if mode == 'preserve' and module not in _modules_with_preserve:
            return True

        if module in self._modules_with_create:
            create = task["action"].get("create", self._modules_with_create[module])
            return create and mode is None

        # A file that doesn't exist cannot have a mode
        if task['action'].get('state', None) == "absent":
            return False

        # A symlink always has mode 0777
        if task['action'].get('state', None) == "link":
            return False

        # Recurse on a directory does not allow for an uniform mode
        if task['action'].get('recurse', None):
            return False

        # The file module does not create anything when state==file (default)
        if module == "file" and task['action'].get('state', 'file') == 'file':
            return False

        # replace module is the only one that has a valid default preserve
        # behavior, but we want to trigger rule if user used incorrect
        # documentation and put 'preserve', which is not supported.
        if module == 'replace' and mode is None:
            return False

        return mode is None


if "pytest" in sys.modules:  # noqa: C901
    import pytest

    SUCCESS_PERMISSIONS_PRESENT = '''
- hosts: all
  tasks:
    - name: permissions not missing and numeric
      file:
        path: foo
        mode: 0600
'''

    SUCCESS_ABSENT_STATE = '''
- hosts: all
  tasks:
    - name: permissions missing while state is absent is fine
      file:
        path: foo
        state: absent
'''

    SUCCESS_DEFAULT_STATE = '''
- hosts: all
  tasks:
    - name: permissions missing while state is file (default) is fine
      file:
        path: foo
'''

    SUCCESS_LINK_STATE = '''
- hosts: all
  tasks:
    - name: permissions missing while state is link is fine
      file:
        path: foo2
        src: foo
        state: link
'''

    SUCCESS_CREATE_FALSE = '''
- hosts: all
  tasks:
    - name: file edit when create is false
      lineinfile:
        path: foo
        create: false
        line: some content here
'''

    SUCCESS_REPLACE = '''
- hosts: all
  tasks:
    - name: replace should not require mode
      replace:
        path: foo
'''

    SUCCESS_RECURSE = '''
- hosts: all
  tasks:
    - name: file with recursive does not require mode
      file:
        state: directory
        recurse: yes
    - name: permissions not missing and numeric (fqcn)
      ansible.builtin.file:
        path: bar
        mode: 755
    - name: file edit when create is false (fqcn)
      ansible.builtin.lineinfile:
        path: foo
        create: false
        line: some content here
'''

    FAIL_PRESERVE_MODE = '''
- hosts: all
  tasks:
    - name: file does not allow preserve value for mode
      file:
        path: foo
        mode: preserve
'''

    FAIL_MISSING_PERMISSIONS_TOUCH = '''
- hosts: all
  tasks:
    - name: permissions missing and might create file
      file:
        path: foo
        state: touch
    - name: permissions missing and might create file (fqcn)
      ansible.builtin.file:
        path: foo
        state: touch
'''

    FAIL_MISSING_PERMISSIONS_DIRECTORY = '''
- hosts: all
  tasks:
    - name: permissions missing and might create directory
      file:
        path: foo
        state: directory
    - name: lineinfile when create is true (fqcn)
      ansible.builtin.lineinfile:
        path: foo
        create: true
        line: some content here
'''

    FAIL_LINEINFILE_CREATE = '''
- hosts: all
  tasks:
    - name: lineinfile when create is true
      lineinfile:
        path: foo
        create: true
        line: some content here
'''

    FAIL_REPLACE_PRESERVE = '''
- hosts: all
  tasks:
    - name: replace does not allow preserve mode
      replace:
        path: foo
        mode: preserve
'''

    FAIL_PERMISSION_COMMENT = '''
- hosts: all
  tasks:
    - name: permissions is only a comment
      file:
        path: foo
        owner: root
        group: root
        state: directory
        # mode: 0755
'''

    FAIL_INI_PERMISSION = '''
- hosts: all
    tasks:
     - name: permissions needed if create is used
       ini_file:
         path: foo
         create: true
'''

    FAIL_INI_PRESERVE = '''
- hosts: all
  tasks:
    - name: ini_file does not accept preserve mode
      ini_file:
        path: foo
        create: true
        mode: preserve
'''

    @pytest.mark.parametrize(
        'rule_runner', (MissingFilePermissionsRule,), indirect=['rule_runner']
    )
    def test_success_permissions_present(rule_runner: RunFromText) -> None:
        """Permissions present and numeric."""
        results = rule_runner.run_playbook(SUCCESS_PERMISSIONS_PRESENT)
        assert len(results) == 0

    @pytest.mark.parametrize(
        'rule_runner', (MissingFilePermissionsRule,), indirect=['rule_runner']
    )
    def test_success_absent_state(rule_runner: RunFromText) -> None:
        """No permissions required if file is absent."""
        results = rule_runner.run_playbook(SUCCESS_ABSENT_STATE)
        assert len(results) == 0

    @pytest.mark.parametrize(
        'rule_runner', (MissingFilePermissionsRule,), indirect=['rule_runner']
    )
    def test_success_default_state(rule_runner: RunFromText) -> None:
        """No permissions required if default state."""
        results = rule_runner.run_playbook(SUCCESS_DEFAULT_STATE)
        assert len(results) == 0

    @pytest.mark.parametrize(
        'rule_runner', (MissingFilePermissionsRule,), indirect=['rule_runner']
    )
    def test_success_link_state(rule_runner: RunFromText) -> None:
        """No permissions required if it is a link."""
        results = rule_runner.run_playbook(SUCCESS_LINK_STATE)
        assert len(results) == 0

    @pytest.mark.parametrize(
        'rule_runner', (MissingFilePermissionsRule,), indirect=['rule_runner']
    )
    def test_success_create_false(rule_runner: RunFromText) -> None:
        """No permissions required if file is not created."""
        results = rule_runner.run_playbook(SUCCESS_CREATE_FALSE)
        assert len(results) == 0

    @pytest.mark.parametrize(
        'rule_runner', (MissingFilePermissionsRule,), indirect=['rule_runner']
    )
    def test_success_replace(rule_runner: RunFromText) -> None:
        """Replacing a file do not require mode."""
        results = rule_runner.run_playbook(SUCCESS_REPLACE)
        assert len(results) == 0

    @pytest.mark.parametrize(
        'rule_runner', (MissingFilePermissionsRule,), indirect=['rule_runner']
    )
    def test_success_recurse(rule_runner: RunFromText) -> None:
        """Do not require mode when recursing."""
        results = rule_runner.run_playbook(SUCCESS_RECURSE)
        assert len(results) == 0

    @pytest.mark.parametrize(
        'rule_runner', (MissingFilePermissionsRule,), indirect=['rule_runner']
    )
    def test_fail_preserve_mode(rule_runner: RunFromText) -> None:
        """File does not allow preserve value for mode."""
        results = rule_runner.run_playbook(FAIL_PRESERVE_MODE)
        assert len(results) == 1

    @pytest.mark.parametrize(
        'rule_runner', (MissingFilePermissionsRule,), indirect=['rule_runner']
    )
    def test_fail_missing_permissions_touch(rule_runner: RunFromText) -> None:
        """Missing permissions when possibly creating file."""
        results = rule_runner.run_playbook(FAIL_MISSING_PERMISSIONS_TOUCH)
        assert len(results) == 2

    @pytest.mark.parametrize(
        'rule_runner', (MissingFilePermissionsRule,), indirect=['rule_runner']
    )
    def test_fail_missing_permissions_directory(rule_runner: RunFromText) -> None:
        """Missing permissions when possibly creating a directory."""
        results = rule_runner.run_playbook(FAIL_MISSING_PERMISSIONS_DIRECTORY)
        assert len(results) == 2

    @pytest.mark.parametrize(
        'rule_runner', (MissingFilePermissionsRule,), indirect=['rule_runner']
    )
    def test_fail_lineinfile_create(rule_runner: RunFromText) -> None:
        """Lineinfile might create a file."""
        results = rule_runner.run_playbook(FAIL_LINEINFILE_CREATE)
        assert len(results) == 1

    @pytest.mark.parametrize(
        'rule_runner', (MissingFilePermissionsRule,), indirect=['rule_runner']
    )
    def test_fail_replace_preserve(rule_runner: RunFromText) -> None:
        """Replace does not allow preserve mode."""
        results = rule_runner.run_playbook(FAIL_REPLACE_PRESERVE)
        assert len(results) == 1

    @pytest.mark.parametrize(
        'rule_runner', (MissingFilePermissionsRule,), indirect=['rule_runner']
    )
    def test_fail_permission_comment(rule_runner: RunFromText) -> None:
        """Permissions is only a comment."""
        results = rule_runner.run_playbook(FAIL_PERMISSION_COMMENT)
        assert len(results) == 1

    @pytest.mark.parametrize(
        'rule_runner', (MissingFilePermissionsRule,), indirect=['rule_runner']
    )
    def test_fail_ini_permission(rule_runner: RunFromText) -> None:
        """Permissions needed if create is used."""
        results = rule_runner.run_playbook(FAIL_INI_PERMISSION)
        assert len(results) == 1

    @pytest.mark.parametrize(
        'rule_runner', (MissingFilePermissionsRule,), indirect=['rule_runner']
    )
    def test_fail_ini_preserve(rule_runner: RunFromText) -> None:
        """The ini_file module does not accept preserve mode."""
        results = rule_runner.run_playbook(FAIL_INI_PRESERVE)
        assert len(results) == 1
