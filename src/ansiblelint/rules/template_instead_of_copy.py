"""Implementation of template-instead-of-copy rule."""
# Copyright (c) 2022, Alexander Skiba
# references
# - github discussion of issue: https://github.com/ansible/ansible/issues/50580
# - ansible docs with warning: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/copy_module.html#synopsis

from typing import TYPE_CHECKING, Any, Dict, Union

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from typing import Optional

    from ansiblelint.file_utils import Lintable


class UseTemplateInsteadOfCopyRule(AnsibleLintRule):
    id = 'template-instead-of-copy'
    shortdesc = 'Templated files should use template instead of copy'
    description = (
        'Items which are templated should use ``template`` instead of '
        '``copy`` with ``content`` to ensure correctness.'
    )
    severity = 'MEDIUM'
    tags = ['unpredictability']
    version_added = 'custom'

    def matchtask(
        self, task: Dict[str, Any], file: 'Optional[Lintable]' = None
    ) -> Union[bool, str]:
        if task['action']['__ansible_module__'] == 'copy':
            if task['action'].get('content'):
                return True
        return False
