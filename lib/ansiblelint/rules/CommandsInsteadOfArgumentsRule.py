import ansiblelint.utils
import os
from ansiblelint import AnsibleLintRule

class CommandsInsteadOfArgumentsRule(AnsibleLintRule):
    id = 'ANSIBLE0007'
    shortdesc = 'Using command rather than an argument to e.g. file'
    description = 'Executing a command when there is are arguments to modules ' + \
                  'is generally a bad idea'
    tags = ['resources']

    _commands = [ 'command', 'shell', 'raw' ]
    _arguments = { 'chown': 'owner', 'chmod': 'mode', 'chgrp': 'group',
                   'ln': 'state=link', 'mkdir': 'state=directory',
                   'rmdir': 'state=absent', 'rm': 'state=absent' }


    def matchtask(self, file, task):
        if task["action"]["module"] in self._commands:
            executable = os.path.basename(task["action"]["args"][0])
            if self._arguments.has_key(executable):
                message = "{} used in place of argument {} to file module"
                return message.format(executable, self._arguments[executable])
