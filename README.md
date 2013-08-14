Ansible-lint
============

ansible-lint checks playbooks for practices and behaviour that could
potentially be improved

WARNING
-------

I am using documentation-driven development to produce the first version of
ansible-lint. This is at present a work in progress. This is on github as
I see no point in concealing this work, but at present, there is not yet even
a binary!

Usage
-----

```
Usage: ansible-lint playbook.yml

Options:
  --version      show program's version number and exit
  -h, --help     show this help message and exit
  -c CONFIGFILE  location of configuration file
  -r RULESDIR    location of rules directory
  -i INVENTORY   specify inventory host file
  -t TAGS        only check rules tagged with these values
  -x SKIP_TAGS   only check rules whose tags do not match these values
```

Rules
=====

Rules are described using a class file per rule. 
Default rules are named ansible0001.py etc. 

Each rule definition should have the following:
* ID: A unique identifier
* Description: Behaviour the rule is looking for
* Tags: one or more tags that may be used to include or exclude the rule
* A method ```prematch``` that takes an unparsed playbook and returns an 
array of matching lines
* A method ```postmatch``` that takes a parsed playbook and returns an array 
of matching lines

An example rule is
```
from ansiblelint import AnsibleLintRule
from ansiblelint import RulesCollection

class Ansible0001(AnsibleLintRule):

    ID = 'ANSIBLE0001'
    DESCRIPTION = 'Deprecated variable declarations'
    TAGS = [ 'deprecated' ]

    def __init__(self):
        super(Ansible0001, self).__init__(id=Ansible0001.ID, 
                                          description=Ansible0001.DESCRIPTION, 
                                          tags=Ansible0001.TAGS)

    def prematch(self, playbook):
        return ansiblelint.utils.matchlines(playbook, lambda x: '${' in x)

RulesCollection.register(Ansible0001())
```
