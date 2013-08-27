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
    _modules = [ 'git', 'hg', 'curl', 'wget', 'svn', 'ln', 'cp', 'service', 'mount' ]


    def _command_matcher(self, line):
        tokens = ansiblelint.utils.tokenize(line)
        return tokens[0] in self._commands and os.path.basename(tokens[1]) in self._modules


    def match(self,playbook):
        return ansiblelint.utils.matchlines(playbook, self._command_matcher)
                
