# Copyright (c) 2020, Joachim Lusiardi
# Copyright (c) 2020, Ansible Project

import os.path
from typing import TYPE_CHECKING, List

import ansible.parsing.yaml.objects

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable


class IncludeMissingFileRule(AnsibleLintRule):
    id = '505'
    shortdesc = 'referenced files must exist'
    description = (
        'All files referenced by by include / import tasks '
        'must exist. The check excludes files with jinja2 '
        'templates in the filename.'
    )
    severity = 'MEDIUM'
    tags = ['task', 'bug']
    version_added = 'v4.3.0'

    def matchplay(self, file: "Lintable", data) -> List["MatchError"]:
        results = []

        # avoid failing with a playbook having tasks: null
        for task in (data.get('tasks', []) or []):

            # ignore None tasks or
            # if the id of the current rule is not in list of skipped rules for this play
            if not task or self.id in task.get('skipped_rules', ()):
                continue

            # collect information which file was referenced for include / import
            referenced_file = None
            for key, val in task.items():
                if not (key.startswith('include_') or
                        key.startswith('import_') or
                        key == 'include'):
                    continue
                if isinstance(val, ansible.parsing.yaml.objects.AnsibleMapping):
                    referenced_file = val.get('file', None)
                else:
                    referenced_file = val
                # take the file and skip the remaining keys
                if referenced_file:
                    break

            if referenced_file is None or file.dir is None:
                continue

            # make sure we have a absolute path here and check if it is a file
            referenced_file = os.path.join(file.dir, referenced_file)

            # skip if this is a jinja2 templated reference
            if '{{' in referenced_file:
                continue

            # existing files do not produce any error
            if os.path.isfile(referenced_file):
                continue

            results.append(
                self.create_matcherror(
                    filename=task['__file__'],
                    linenumber=task['__line__'],
                    details=referenced_file))
        return results
