Ansible-lint
============

ansible-lint checks playbooks for practices and behaviour that could
potentially be improved

Setup
-----

Using pip:
```
pip install ansible-lint
```

From source:
```
git clone https://github.com/willthames/ansible-lint
export PYTHONPATH=$PYTHONPATH:`pwd`/ansible-lint/lib
export PATH=$PATH:`pwd`/ansible-lint/bin
```

Usage
-----

```
Usage: ansible-lint playbook.yml

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -L                    list all the rules
  -q                    quieter, although not silent output
  -p                    parseable output in the format of pep8
  -r RULESDIR           specify one or more rules directories using one or
                        more -r arguments. Any -r flags override the default
                        rules in ['/path/to/ansible-
                        lint/lib/ansiblelint/rules'], unless -R is also used.
  -R                    Use default rules ['/path/to/ansible-
                        lint/lib/ansiblelint/rules'] in addition to any extra
                        rules directories specified with -r. There is no need
                        to specify this if no -r flags are used
  -t TAGS               only check rules whose id/tags match these values
  -T                    list all the tags
  -x SKIP_LIST          only check rules whose id/tags do not match these
                        values
  --exclude=EXCLUDE_PATHS
                        path to directories or files to skip. This option is
                        repeatable.
```

False positives
===============

Some rules are a bit of a rule of thumb. Advanced git, yum or apt usage,
for example, is typically difficult to achieve through the modules. In
this case, you should mark the task so that warnings aren't produced.

There are two mechanisms for this - one works with all tasks, the other
works with the command checking modules.

Use the `warn` parameter with the command or shell module.

Use `skip_ansible_lint` tag with any task that you want to skip.

I recommend commenting the reasons why you're skipping the check.
Unfortunately ansible-lint is unable to check for such comments
at this time! (patches welcome)

```
- name: this would typically fire CommandsInsteadOfArgumentRule
  command: warn=no chmod 644 X

- name: this would typically fire CommandsInsteadOfModuleRule
  command: git pull --rebase
  args:
    warn: False

- name: this would typically fire GitHasVersionRule
  git: src=/path/to/git/repo dest=checkout 
  tags:
  - skip_ansible_lint
```

Rules
=====

Rules are described using a class file per rule.
Default rules are named `DeprecatedVariableRule.py`, etc.

Each rule definition should have the following:
* ID: A unique identifier
* Short description: Brief description of the rule
* Description: Behaviour the rule is looking for
* Tags: one or more tags that may be used to include or exclude the rule
* At least one of the following methods:
  * `match` that takes a line and returns `None` or `False` if
  the line doesn't match the test and `True` or a custom message (this
  allows one rule to test multiple behaviours - see e.g. the
  CommandsInsteadOfModulesRule
  * `matchblock` that takes the details about the file and a block.
  It returns `None` or `False` if the line doesn't match the test
  and `True` or a custom message.

An example rule using `match` is:

```python
from ansiblelint import AnsibleLintRule

class DeprecatedVariableRule(AnsibleLintRule):

    id = 'ANSIBLE0001'
    shortdesc = 'Deprecated variable declarations'
    description = 'Check for lines that have old style ${var} ' + \
                  'declarations'
    tags = { 'deprecated' }


    def match(self, file, line):
        return '${' in line
```

An example rule using `matchtask` is:

```python
import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class TaskHasTag(AnsibleLintRule):
    id = 'ANSIBLE0008'
    shortdesc = 'Tasks must have tag'
    description = 'Tasks must have tag'
    tags = ['productivity']


    def matchtask(self, file, task):
        # If the task include another task or make the playbook fail
        # Don't force to have a tag
        if not set(task.keys()).isdisjoint(['include','fail']):
            return False

        # Task should have tags
        if not task.has_key('tags'):
              return True

        return False
```

The `task` argument to `matchtask` contains a number of keys - the critical one is `action`.
The value of `task['action']` contains the module being used, and the arguments passed, both
as key-value pairs and a list of other arguments (e.g. the command used with `shell`)

In ansible-lint 2.0.0, `task['action']['args']` was renamed `task['action']['module_arguments']`
to avoid a clash when a module actually takes `args` as a parameter key (e.g. `ec2_tag`)
Examples
--------

There are some example playbooks with undesirable features. Running
ansible-lint on them works:

```
$ ansible-lint examples/example.yml
[ANSIBLE0004] Git checkouts must contain explicit version
examples/example.yml:15
Task/Handler: git check

[ANSIBLE0004] Git checkouts must contain explicit version
examples/example.yml:18
Task/Handler: git check 2

[ANSIBLE0004] Git checkouts must contain explicit version
examples/example.yml:30
Task/Handler: using git module

[ANSIBLE0002] Trailing whitespace
examples/example.yml:13
    action: do nothing   

[ANSIBLE0002] Trailing whitespace
examples/example.yml:35
    with_items: 

[ANSIBLE0006] git used in place of git module
examples/example.yml:24
Task/Handler: executing git through command

[ANSIBLE0006] git used in place of git module
examples/example.yml:27
Task/Handler: executing git through command

```

If playbooks include other playbooks, or tasks, or handlers or roles, these
are also handled:

```
$ bin/ansible-lint examples/include.yml
[ANSIBLE0004] Checkouts must contain explicit version
/Users/will/src/ansible-lint/examples/roles/bobbins/tasks/main.yml:3
action: git a=b c=d
```

Contributing
============

Please read
[CONTRIBUTING.md](https://github.com/willthames/ansible-lint/blob/master/CONTRIBUTING.md) if you wish to contribute.
