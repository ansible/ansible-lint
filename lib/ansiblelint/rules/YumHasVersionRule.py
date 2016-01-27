import ansiblelint.utils
from ansiblelint import AnsibleLintRule
import re


class YumHasVersionRule(AnsibleLintRule):
    id = 'ANSIBLE1003'
    shortdesc = 'Yum installing package without explicit version'
    description = 'When installing packages be explicit with ' + \
                  'version. This helps create a reproducable ' + \
                  'environment and limits the impact from ' + \
                  'unexpected changes to the system'
    tags = ['repeatability']

    _pattern = '.*\-[0-9]+(\.[0-9]+)*$'
    _variable_pattern = '\{\{.*\}\}'

    def matchtask(self, file, task):
        if task['action']['module'] == 'yum':
            name = task['action'].get('name')
            if(name is not None and not re.match(self._pattern, name) and
               not re.match(self._variable_pattern, name)):
               message = 'Yum package {0} should be installed with ' +\
                         'explicit version'
               return message.format(name)
