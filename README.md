Ansible-lint
============

ansible-lint checks playbooks for practices and behaviour that could
potentially be improved

Usage
-----

```ansible-lint [ -c configfile ] [ -r rulesdir ] [ -i inventory ] [ -t tag1,tag2 ] [ -x excludetag1,excludetag2 ] playbook```

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
from ansible.lint.rule import AnsibleLintRule
from ansible.lint.rule import RulesCollection

class Ansible0001(AnsibleLintRule):

    ID = 'ANSIBLE0001'
    DESCRIPTION = 'Deprecated variable declarations'
    TAGS = [ 'deprecated' ]

    def __init__(self):
        self.super(id=ID, description=DESCRIPTION, tags=TAGS)

    def prematch(self, playbook):
        result = []
        for (lineno, line) in playbook.split("\n").enumerate():
            if '${' in line:
                result.push(lineno)
        return result

RulesCollection.getInstance().register(Ansible0001.new())
```
