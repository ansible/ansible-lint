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
from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable


# Despite documentation mentioning 'preserve' only these modules support it:
_modules_with_preserve = (
    "copy",
    "template",
)

_MODULES: set[str] = {
    "archive",
    "community.general.archive",
    "assemble",
    "ansible.builtin.assemble",
    "copy",  # supports preserve
    "ansible.builtin.copy",
    "file",
    "ansible.builtin.file",
    "get_url",
    "ansible.builtin.get_url",
    "replace",  # implicit preserve behavior but mode: preserve is invalid
    "ansible.builtin.replace",
    "template",  # supports preserve
    "ansible.builtin.template",
    # 'unarchive',  # disabled because .tar.gz files can have permissions inside
}

_MODULES_WITH_CREATE: dict[str, bool] = {
    "blockinfile": False,
    "ansible.builtin.blockinfile": False,
    "htpasswd": True,
    "community.general.htpasswd": True,
    "ini_file": True,
    "community.general.ini_file": True,
    "lineinfile": False,
    "ansible.builtin.lineinfile": False,
}


class MissingFilePermissionsRule(AnsibleLintRule):
    """File permissions unset or incorrect."""

    id = "risky-file-permissions"
    description = (
        "Missing or unsupported mode parameter can cause unexpected file "
        "permissions based "
        "on version of Ansible being used. Be explicit, like `mode: 0644` to "
        "avoid hitting this rule. Special `preserve` value is accepted "
        f"only by {', '.join([f'`{x}`' for x in _modules_with_preserve])} modules."
    )
    link = "https://github.com/ansible/ansible/issues/71200"
    severity = "VERY_HIGH"
    tags = ["unpredictability", "experimental"]
    version_added = "v4.3.0"

    _modules = _MODULES
    _modules_with_create = _MODULES_WITH_CREATE

    # pylint: disable=too-many-return-statements
    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> bool | str:
        module = task["action"]["__ansible_module__"]
        mode = task["action"].get("mode", None)

        if module not in self._modules and module not in self._modules_with_create:
            return False

        if mode == "preserve" and module not in _modules_with_preserve:
            return True

        if module in self._modules_with_create:
            create = task["action"].get("create", self._modules_with_create[module])
            return create and mode is None

        # A file that doesn't exist cannot have a mode
        if task["action"].get("state", None) == "absent":
            return False

        # A symlink always has mode 0777
        if task["action"].get("state", None) == "link":
            return False

        # Recurse on a directory does not allow for an uniform mode
        if task["action"].get("recurse", None):
            return False

        # The file module does not create anything when state==file (default)
        if module == "file" and task["action"].get("state", "file") == "file":
            return False

        # replace module is the only one that has a valid default preserve
        # behavior, but we want to trigger rule if user used incorrect
        # documentation and put 'preserve', which is not supported.
        if module == "replace" and mode is None:
            return False

        return mode is None


if "pytest" in sys.modules:  # noqa: C901
    import pytest

    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.testing import RunFromText  # pylint: disable=ungrouped-imports

    @pytest.mark.parametrize(
        ("file", "expected"),
        (
            pytest.param(
                "examples/playbooks/rule-risky-file-permissions-pass.yml", 0, id="pass"
            ),
            pytest.param(
                "examples/playbooks/rule-risky-file-permissions-fail.yml",
                11,
                id="fails",
            ),
        ),
    )
    def test_risky_file_permissions(file: str, expected: int) -> None:
        """The ini_file module does not accept preserve mode."""
        collection = RulesCollection()
        collection.register(MissingFilePermissionsRule())
        runner = RunFromText(collection)
        results = runner.run(file)
        assert len(results) == expected
        for result in results:
            assert result.tag == "risky-file-permissions"
