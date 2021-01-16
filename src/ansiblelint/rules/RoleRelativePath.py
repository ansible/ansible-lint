# Copyright (c) 2016, Tsukinowa Inc. <info@tsukinowa.jp>
# Copyright (c) 2018, Ansible Project

from ansiblelint.rules import AnsibleLintRule


class RoleRelativePath(AnsibleLintRule):
    id = '404'
    shortdesc = "Doesn't need a relative path in role"
    description = '``copy`` and ``template`` do not need to use relative path for ``src``'
    severity = 'HIGH'
    tags = ['module']
    version_added = 'v4.0.0'

    _module_to_path_folder = {
        'copy': 'files',
        'win_copy': 'files',
        'template': 'templates',
        'win_template': 'win_templates',
    }

    def matchtask(self, file, task):
        module = task['action']['__ansible_module__']
        if module not in self._module_to_path_folder:
            return False

        if 'src' not in task['action']:
            return False

        path_to_check = '../{}'.format(self._module_to_path_folder[module])
        if path_to_check in task['action']['src']:
            return True
