"""Implementation of no-relative-paths rule."""
# Copyright (c) 2016, Tsukinowa Inc. <info@tsukinowa.jp>
# Copyright (c) 2018, Ansible Project

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable


class RoleRelativePath(AnsibleLintRule):
    """The src argument should not use a relative path."""

    id = "no-relative-paths"
    description = "The ``copy`` and ``template`` modules should not use relative path for ``src``."
    severity = "HIGH"
    tags = ["idiom"]
    version_added = "v4.0.0"

    _module_to_path_folder = {
        "copy": "files",
        "win_copy": "files",
        "template": "templates",
        "win_template": "win_templates",
    }

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> bool | str:
        module = task["action"]["__ansible_module__"]
        if module not in self._module_to_path_folder:
            return False

        if "src" not in task["action"]:
            return False

        path_to_check = f"../{self._module_to_path_folder[module]}"
        if path_to_check in task["action"]["src"]:
            return True

        return False
