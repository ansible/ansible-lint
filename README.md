Ansible-lint
============

ansible-lint checks playbooks for practices and behaviour that could
potentially be improved

Usage
-----

```
Usage: ansible-lint playbook.yml

Options:
  --version     show program's version number and exit
  -h, --help    show this help message and exit
  -L            list all the rules
  -q            quieter, although not silent output
  -r RULESDIR   location of rules directory
  -t TAGS       only check rules tagged with these values
  -x SKIP_TAGS  only check rules whose tags do not match these values
```

Rules
=====

Rules are described using a class file per rule. 
Default rules are named DeprecatedVariableRule.py etc. 

Each rule definition should have the following:
* ID: A unique identifier
* Short description: Brief description of the rule
* Description: Behaviour the rule is looking for
* Tags: one or more tags that may be used to include or exclude the rule
* A method ```match``` that takes an unparsed playbook and returns an 
array of matching lines

An example rule is
```
from ansiblelint import AnsibleLintRule
from ansiblelint import RulesCollection

class DeprecatedVariableRule(AnsibleLintRule):

    id = 'ANSIBLE0001'
    shortdesc = 'Deprecated variable declarations' 
    description = 'Check for lines that have old style ${var} ' + \
                  'declarations'
    tags = { 'deprecated' }


    def match(self, playbook):
        return ansiblelint.utils.matchlines(playbook, lambda x: '${' in x)
```
