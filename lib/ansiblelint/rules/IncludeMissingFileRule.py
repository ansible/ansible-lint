# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project

from __future__ import print_function
from ansiblelint import AnsibleLintRule
import os.path
import ansible.parsing.yaml.objects


class IncludeMissingFileRule(AnsibleLintRule):
    id = '4711'
    shortdesc = 'an include task references a non existent file'
    description = 'Tabs can cause unexpected display issues, use spaces'
    severity = 'HIGH'
    tags = ['formatting']
    version_added = 'v4.2.0'

    def matchplay(self, file, data):
        abs_path = file.get('abs_path', None)
        results = []
        for task in data.get('tasks', []):

            # check if the id of the current rule is not in list of skipped rules for this play
            if self.id in task['skipped_rules']:
                continue

            # collect information which file was referenced for include / import
            referenced_file = None
            for key in task.keys():
                if key.startswith('include_') or key.startswith('import_') or key == 'include':
                    tmp = task[key]
                    if isinstance(tmp, ansible.parsing.yaml.objects.AnsibleMapping):
                        referenced_file = tmp.get('file', None)
                    else:
                        referenced_file = tmp

            if referenced_file:
                # make sure we have a absolute path here and check if it is a file
                referenced_file = os.path.join(abs_path, referenced_file)
                if not os.path.isfile(referenced_file):
                    results.append(({'referenced_file': referenced_file},
                                    'referenced missing file in %s:%i'
                                    % (task['__file__'], task['__line__'])))
        return results
