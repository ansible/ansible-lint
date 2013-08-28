import ansiblelint.utils
import os
from ansiblelint import AnsibleLintRule

class CommandsInsteadOfModulesRule(AnsibleLintRule):
    id = 'ANSIBLE0006'
    shortdesc = 'Using command rather than module'
    description = 'Executing a command when there is an Ansible module ' + \
                  'is generally a bad idea'
    tags = {'resources'}

    _commands = [ 'command', 'shell', 'raw' ]
    _modules = { 'git': 'git', 'hg': 'hg', 'curl': 'get_url', 'wget': 'get_url', 
                 'svn': 'subversion', 'cp': 'copy', 'service': 'service', 
                  'mount': 'mount', 'rpm': 'yum', 'yum': 'yum', 'apt-get': 'apt-get' }


    def match(self, line):
        (command, args, kwargs) = ansiblelint.utils.tokenize(line)
        if args == []:
            return None
        executable = os.path.basename(args[0])
        if command in self._commands and self._modules.has_key(executable):
            message = "{} used in place of {} module"
            return message.format(executable, self._modules[executable])
