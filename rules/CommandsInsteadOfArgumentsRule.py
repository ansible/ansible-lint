import ansiblelint.utils
import os
from ansiblelint import AnsibleLintRule

class CommandsInsteadOfArgumentsRule(AnsibleLintRule):
    id = 'ANSIBLE0007'
    shortdesc = 'Using command rather than an argument to e.g. file'
    description = 'Executing a command when there is are arguments to modules ' + \
                  'is generally a bad idea'
    tags = {'resources'}

    _commands = [ 'command', 'shell', 'raw' ]
    _arguments = [ 'chown', 'chmod', 'chgrp' ]


    def _command_matcher(self, line):
        tokens = ansiblelint.utils.tokenize(line)
        return tokens[0] in self._commands and os.path.basename(tokens[1]) in self._arguments


    def match(self,playbook):
        return ansiblelint.utils.matchlines(playbook, self._command_matcher)
