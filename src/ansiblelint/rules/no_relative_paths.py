"""Implementation of no-relative-paths rule."""

# Copyright (c) 2016, Tsukinowa Inc. <info@tsukinowa.jp>
# Copyright (c) 2018, Ansible Project

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task


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
        self,
        task: Task,
        file: Lintable | None = None,
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


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    import pytest

    # pylint: disable=ungrouped-imports
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    @pytest.mark.parametrize(
        ("test_file", "failures"),
        (
            pytest.param("examples/playbooks/no_relative_paths_fail.yml", 2, id="fail"),
            pytest.param("examples/playbooks/no_relative_paths_pass.yml", 0, id="pass"),
        ),
    )
    def test_no_relative_paths(
        default_rules_collection: RulesCollection,
        test_file: str,
        failures: int,
    ) -> None:
        """Test rule matches."""
        results = Runner(test_file, rules=default_rules_collection).run()
        assert len(results) == failures
        for result in results:
            assert result.tag == "no-relative-paths"
