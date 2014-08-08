import ansiblelint.utils
import os
from ansiblelint import AnsibleLintRule

class CommandsInsteadOfModulesRule(AnsibleLintRule):
    id = 'ANSIBLE0006'
    shortdesc = 'Using command rather than module'
    description = 'Executing a command when there is an Ansible module ' + \
                  'is generally a bad idea'
    tags = ['resources']

    _commands = [ 'command', 'shell', 'raw' ]
    _modules = { 'git': 'git', 'hg': 'hg', 'curl': 'get_url', 'wget': 'get_url', 
                 'svn': 'subversion', 'cp': 'copy', 'service': 'service', 
                  'mount': 'mount', 'rpm': 'yum', 'yum': 'yum', 'apt-get': 'apt-get',
                  'unzip': 'unarchive', 'tar': 'unarchive' }


    def matchtask(self, file, task):
        if task["action"]["module"] in self._commands:
            executable = os.path.basename(task["action"]["args"][0])
            if self._modules.has_key(executable):
                message = "{0} used in place of {1} module"
                return message.format(executable, self._modules[executable])
