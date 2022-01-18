# Copyright (c) 2016, Tsukinowa Inc. <info@tsukinowa.jp>
# Copyright (c) 2018, Ansible Project

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from ansiblelint.rules import AnsibleLintRule, TransformMixin

if TYPE_CHECKING:
    from ruamel.yaml.comments import CommentedMap, CommentedSeq

    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable


class RoleRelativePath(AnsibleLintRule, TransformMixin):
    id = 'no-relative-paths'
    shortdesc = "Doesn't need a relative path in role"
    description = (
        '``copy`` and ``template`` do not need to use relative path for ``src``'
    )
    severity = 'HIGH'
    tags = ['idiom']
    version_added = 'v4.0.0'

    _module_to_path_folder = {
        'copy': 'files',
        'win_copy': 'files',
        'template': 'templates',
        'win_template': 'win_templates',
    }

    def matchtask(
        self, task: Dict[str, Any], file: 'Optional[Lintable]' = None
    ) -> Union[bool, str]:
        module = task['action']['__ansible_module__']
        if module not in self._module_to_path_folder:
            return False

        if 'src' not in task['action']:
            return False

        path_to_check = '../{}'.format(self._module_to_path_folder[module])
        if path_to_check in task['action']['src']:
            return True

        return False

    def transform(
        self,
        match: "MatchError",
        lintable: "Lintable",
        data: "Union[CommentedMap, CommentedSeq, str]",
    ) -> None:
        """Transform data to fix the MatchError."""
        if not match.task:
            # a safety check based on mypy error
            return
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
