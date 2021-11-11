import os
from typing import Any, Union

from ruamel.yaml.comments import CommentedMap, CommentedSeq

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules.UsingBareVariablesIsDeprecatedRule import UsingBareVariablesIsDeprecatedRule
from ansiblelint.transforms import Transform


class WrapBareVarsTransform(Transform):
    id = "wrap-bare-vars"
    shortdesc = "Wrap bare vars in {{ }} jinja blocks."
    description = (
        "Using bare variables is deprecated. This updates your "
        "playbooks by wrapping bare vars in jinja braces using"
        "this syntax: ``{{ your_variable }}``"
    )
    version_added = "5.3"

    wants = UsingBareVariablesIsDeprecatedRule
    tags = UsingBareVariablesIsDeprecatedRule.tags
    # noinspection PyProtectedMember
    _jinja = UsingBareVariablesIsDeprecatedRule._jinja
    # noinspection PyProtectedMember
    _glob = UsingBareVariablesIsDeprecatedRule._glob

    def __call__(
        self, match: MatchError, lintable: Lintable, data: Union[CommentedMap, CommentedSeq]
    ) -> None:
        """Transform data to fix the MatchError."""
        target_task = self._seek(match.yaml_path, data)
        loop_type = next((key for key in target_task if key.startswith("with_")), None)
        if not loop_type:
            # We should not get here because the transform only gets tasks that matched.
            # A task without a loop_type would not have matched.
            return
        loop = target_task[loop_type]

        fixed = False
        if isinstance(loop, (list, tuple)):
            for loop_index, loop_item in enumerate(loop):
                if loop_type == "with_subelements" and loop_index > 0:
                    break
                if self._needs_wrap(loop_item, loop_type):
                    target_task[loop_type][loop_index] = self._wrap(loop_item)
                    fixed = True
        elif self._needs_wrap(loop, loop_type):
            target_task[loop_type] = self._wrap(loop)
            fixed = True
        # call self._fixed(match) when data has been transformed to fix the error.
        if fixed:
            self._fixed(match)

    @staticmethod
    def _wrap(expression: str) -> str:
        return "{{ " + expression + " }}"

    def _needs_wrap(self, loop_item: Any, loop_type: str) -> bool:
        if not isinstance(loop_item, str):
            return False
        if loop_type in ["with_sequence", "with_ini", "with_inventory_hostnames"]:
            return False
        if self._jinja.match(loop_item):
            return False
        if loop_type == "with_fileglob":
            return not bool(self._jinja.search(loop_item) or self._glob.search(loop_item))
        if loop_type == 'with_filetree':
            return not bool(self._jinja.search(loop_item) or loop_item.endswith(os.sep))
        return True
