from pathlib import Path
from typing import Union

from ruamel.yaml.comments import CommentedMap, CommentedSeq

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules.RoleRelativePath import RoleRelativePath
from ansiblelint.transforms import Transform


class ResolveRoleRelativePathsTransform(Transform):
    id = "resolve-relative-paths"
    shortdesc = "Wrap bare vars in {{ }} jinja blocks."
    description = (
        "Using bare variables is deprecated. This updates your "
        "playbooks by wrapping bare vars in jinja braces using"
        "this syntax: ``{{ your_variable }}``"
    )
    version_added = "5.3"

    wants = RoleRelativePath
    tags = RoleRelativePath.tags
    # noinspection PyProtectedMember
    _module_to_path_folder = RoleRelativePath._module_to_path_folder

    def __call__(
        self,
        match: MatchError,
        lintable: Lintable,
        data: Union[CommentedMap, CommentedSeq],
    ) -> None:
        """Transform data to fix the MatchError."""
        target_task = self._seek(match.yaml_path, data)
        module = match.task["action"]["__ansible_module__"]
        src_path = Path(target_task[module]["src"])

        default_relative_path = f"../{self._module_to_path_folder[module]}"
        try:
            src = src_path.relative_to(default_relative_path)
        except ValueError:
            # probably a false positive alternate directory.
            # bail. unable to fix.
            return

        target_task[module]["src"] = str(src)
        self._fixed(match)
