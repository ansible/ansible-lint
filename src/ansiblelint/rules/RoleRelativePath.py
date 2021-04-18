# Copyright (c) 2016, Tsukinowa Inc. <info@tsukinowa.jp>
# Copyright (c) 2018, Ansible Project

from typing import TYPE_CHECKING, Any, Dict, Union

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from typing import Optional

    from ansiblelint.file_utils import Lintable


class RoleRelativePath(AnsibleLintRule):
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
